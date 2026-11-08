import json
from types import SimpleNamespace

from phonehome.mitm_metadata import flow_metadata


def test_flow_metadata_omits_secrets_and_query_values():
    flow = SimpleNamespace(
        request=SimpleNamespace(
            pretty_url="https://i.instagram.com/api/v1/feed/timeline/?access_token=secret",
            timestamp_start=1794099600.0,
            method="POST",
            headers={"Authorization": "Bearer secret"},
            raw_content=b'{"password":"secret"}',
        ),
        response=SimpleNamespace(status_code=200, raw_content=b'{"private":"data"}'),
        client_conn=SimpleNamespace(peername=("192.0.2.10", 43123)),
        server_conn=SimpleNamespace(address=("198.51.100.20", 443)),
    )

    record = flow_metadata(flow)
    serialized = json.dumps(record)

    assert record["path"] == "/api/v1/feed/timeline/"
    assert record["request_bytes"] == 21
    assert record["response_bytes"] == 18
    assert "secret" not in serialized
    assert "Authorization" not in serialized
    assert "private" not in serialized
