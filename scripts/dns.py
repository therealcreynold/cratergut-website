#!/usr/bin/env python3
"""Points cratergut.com at GitHub Pages, without throwing away anything else.

Namecheap has no "add one record" call. `namecheap.domains.dns.setHosts` **replaces every
host record on the domain**, so the naive version of this script — send the nine records
GitHub Pages needs — silently deletes the MX records and the domain stops receiving email.
`support@cratergut.com` is printed on the website and filed with Apple as the support
address, so that is not a small mistake.

So this reads what is there, merges, shows you the difference, and changes nothing unless
you ask twice.

    export NAMECHEAP_API_USER=...      # usually the same as the account username
    export NAMECHEAP_USERNAME=...
    export NAMECHEAP_API_KEY=...       # never pass this on the command line
    python3 scripts/dns.py             # shows what it would do
    python3 scripts/dns.py --apply     # does it

The key is read from the environment on purpose. A secret in an argument is a secret in
`ps`, in your shell history, and in any log that records the command.

Two things Namecheap needs before any of this works, both in Profile > Tools > API Access:
API access switched on for the account, and the IP this runs from added to the allowlist.
The script prints that IP.
"""

import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

API = "https://api.namecheap.com/xml.response"
NS = {"nc": "http://api.namecheap.com/xml.response"}

SLD, TLD = "cratergut", "com"

# GitHub Pages, from their own documentation. An apex domain cannot be a CNAME, which is why
# there are eight of these rather than one.
PAGES_A = [
    "185.199.108.153",
    "185.199.109.153",
    "185.199.110.153",
    "185.199.111.153",
]
PAGES_AAAA = [
    "2606:50c0:8000::153",
    "2606:50c0:8001::153",
    "2606:50c0:8002::153",
    "2606:50c0:8003::153",
]
PAGES_WWW = "therealcreynold.github.io"

# What this script owns. Anything matching one of these is replaced; everything else on the
# domain is carried across untouched.
OWNED = {("@", "A"), ("@", "AAAA"), ("@", "ALIAS"), ("@", "URL"), ("@", "URL301"),
         ("@", "FRAME"), ("@", "CNAME"), ("www", "CNAME"), ("www", "A"), ("www", "URL"),
         ("www", "URL301"), ("www", "FRAME")}


def need(name):
    value = os.environ.get(name)
    if not value:
        sys.exit(f"{name} is not set. See the comment at the top of this file.")
    return value


def call(command, extra=None):
    params = {
        "ApiUser": need("NAMECHEAP_API_USER"),
        "ApiKey": need("NAMECHEAP_API_KEY"),
        "UserName": need("NAMECHEAP_USERNAME"),
        "ClientIp": client_ip(),
        "Command": command,
        "SLD": SLD,
        "TLD": TLD,
    }
    params.update(extra or {})
    body = urllib.parse.urlencode(params).encode()
    with urllib.request.urlopen(urllib.request.Request(API, data=body), timeout=60) as r:
        text = r.read().decode()
    root = ET.fromstring(text)
    if root.attrib.get("Status") != "OK":
        errors = [e.text for e in root.iter() if e.tag.endswith("Error")]
        sys.exit("Namecheap refused: " + "; ".join(filter(None, errors) or ["unknown"]))
    return root


_ip = None


def client_ip():
    """The address Namecheap will see, which is the one that has to be on the allowlist."""
    global _ip
    if _ip is None:
        _ip = os.environ.get("NAMECHEAP_CLIENT_IP") or (
            urllib.request.urlopen("https://api.ipify.org", timeout=30).read().decode().strip()
        )
    return _ip


def existing():
    root = call("namecheap.domains.dns.getHosts")
    out = []
    for host in root.iter():
        if not host.tag.endswith("host"):
            continue
        a = host.attrib
        out.append(
            {
                "HostName": a.get("Name", "@"),
                "RecordType": a.get("Type", "A"),
                "Address": a.get("Address", ""),
                "TTL": a.get("TTL", "1800"),
                "MXPref": a.get("MXPref", "10"),
            }
        )
    return out


def desired(current):
    kept = [r for r in current if (r["HostName"], r["RecordType"]) not in OWNED]
    fresh = [{"HostName": "@", "RecordType": "A", "Address": ip, "TTL": "1800"} for ip in PAGES_A]
    fresh += [
        {"HostName": "@", "RecordType": "AAAA", "Address": ip, "TTL": "1800"}
        for ip in PAGES_AAAA
    ]
    fresh += [
        {"HostName": "www", "RecordType": "CNAME", "Address": PAGES_WWW + ".", "TTL": "1800"}
    ]
    return kept + fresh


def show(title, records):
    print(f"\n{title}")
    if not records:
        print("  (none)")
    for r in sorted(records, key=lambda r: (r["RecordType"], r["HostName"], r["Address"])):
        print(f"  {r['RecordType']:<6} {r['HostName']:<20} {r['Address']}")


def main():
    apply = "--apply" in sys.argv
    print(f"Calling as {client_ip()} — this address must be on Namecheap's API allowlist.")

    current = existing()
    show("Currently on the domain:", current)

    dropped = [r for r in current if (r["HostName"], r["RecordType"]) in OWNED]
    carried = [r for r in current if (r["HostName"], r["RecordType"]) not in OWNED]
    new = desired(current)

    show("Being replaced:", dropped)
    show("Carried across untouched:", carried)
    show("Result:", new)

    if not apply:
        print("\nNothing changed. Re-run with --apply to write this.")
        return

    # A domain with no records at all almost certainly means getHosts failed in a way that
    # still returned OK. Writing in that state would wipe the domain.
    if not new:
        sys.exit("Refusing to write an empty record set.")

    payload = {}
    for i, r in enumerate(new, start=1):
        payload[f"HostName{i}"] = r["HostName"]
        payload[f"RecordType{i}"] = r["RecordType"]
        payload[f"Address{i}"] = r["Address"]
        payload[f"TTL{i}"] = r.get("TTL", "1800")
        if r["RecordType"] == "MX":
            payload[f"MXPref{i}"] = r.get("MXPref", "10")

    call("namecheap.domains.dns.setHosts", payload)
    print(f"\nWrote {len(new)} records.")
    print("DNS takes a while. Then, in the repository's Settings > Pages, turn on Enforce")
    print("HTTPS once GitHub has issued a certificate — it can take up to 24 hours to offer.")


if __name__ == "__main__":
    main()
