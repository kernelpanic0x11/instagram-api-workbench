"""Build a deliberately limited record from a decrypted HTTP flow."""
import datetime as dt
from urllib.parse import urlsplit


def _address_host(address):
    if isinstance(address, (tuple, list)) and address:
        return address[0]
    return None


def flow_metadata(flow):
    """Return request metadata without headers, query values, or body content."""
    request = flow.request
    response = getattr(flow, "response", None)
    parsed = urlsplit(request.pretty_url)
    started = dt.datetime.fromtimestamp(request.timestamp_start, dt.timezone.utc)

    return {
        "started_at": started.isoformat(),
        "client_ip": _address_host(getattr(flow.client_conn, "peername", None)),
        "server_ip": _address_host(getattr(flow.server_conn, "address", None)),
        "method": request.method,
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "path": parsed.path or "/",
        "status_code": getattr(response, "status_code", None),
        "request_bytes": len(request.raw_content or b""),
        "response_bytes": len(response.raw_content or b"") if response else None,
    }
