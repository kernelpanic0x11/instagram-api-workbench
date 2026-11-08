"""Mitmproxy addon that writes sanitized HTTP metadata as newline-delimited JSON."""
import json
import os
from pathlib import Path

from phonehome.mitm_metadata import flow_metadata


OUTPUT = Path(os.environ.get("PHONEHOME_MITM_LOG", "runs/mitm-demo/requests.ndjson"))


def _write(flow):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(flow_metadata(flow), separators=(",", ":")) + "\n")


def response(flow):
    _write(flow)


def error(flow):
    _write(flow)
