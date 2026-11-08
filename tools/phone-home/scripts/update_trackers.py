#!/usr/bin/env python3
"""Refresh Disconnect's tracker list; review its license before use."""
import json
from pathlib import Path
from urllib.request import urlopen

URL = "https://raw.githubusercontent.com/disconnectme/disconnect-tracking-protection/master/services.json"
DESTINATION = Path(__file__).resolve().parents[1] / "phonehome/data/services.json"


def main():
    with urlopen(URL, timeout=30) as response:
        data = response.read()
    parsed = json.loads(data)
    if not isinstance(parsed, dict) or "categories" not in parsed:
        raise ValueError("Unexpected Disconnect list format")
    temporary = DESTINATION.with_suffix(".json.tmp")
    temporary.write_bytes(data)
    temporary.replace(DESTINATION)
    print(f"Updated {DESTINATION} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
