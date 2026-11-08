import datetime as dt
from phonehome.capture import fetch_queries


def test_dns_excludes_other_clients_and_outside_window(monkeypatch):
    start = dt.datetime(2026, 11, 7, 12, tzinfo=dt.timezone.utc)
    end = start + dt.timedelta(seconds=20)
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {'data': [
                {'client': '192.0.2.10', 'time': '2026-11-07T12:00:10Z'},
                {'client': '192.0.2.11', 'time': '2026-11-07T12:00:10Z'},
                {'client': '192.0.2.10', 'time': '2026-11-07T11:59:59Z'},
            ], 'oldest': '2026-11-07T11:59:59Z'}
    monkeypatch.setattr('phonehome.capture.requests.get', lambda *a, **kw: Response())
    result = fetch_queries('192.0.2.10', start, end,
                           {'ADGUARD_USERNAME': 'test', 'ADGUARD_PASSWORD': 'test'})
    assert result['error'] is None
    assert len(result['entries']) == 1
    assert result['entries'][0]['client'] == '192.0.2.10'


def test_dns_follows_empty_filtered_page_cursor(monkeypatch):
    start = dt.datetime(2026, 11, 7, 12, tzinfo=dt.timezone.utc)
    end = start + dt.timedelta(seconds=20)
    calls = []
    match = {'client': '192.0.2.10', 'time': '2026-11-07T12:00:10Z'}
    pages = [
        {'data': [], 'oldest': '2026-11-07T12:00:15Z'},
        {'data': [match], 'oldest': ''},
    ]

    class Response:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self.data

    def get(*args, **kwargs):
        calls.append(kwargs['params'])
        return Response(pages[len(calls) - 1])

    monkeypatch.setattr('phonehome.capture.requests.get', get)
    result = fetch_queries('192.0.2.10', start, end,
                           {'ADGUARD_USERNAME': 'test', 'ADGUARD_PASSWORD': 'test'})
    assert result == {'entries': [match], 'error': None}
    assert len(calls) == 2
    assert calls[1]['older_than'] == '2026-11-07T12:00:15Z'


import importlib
import json
import signal
import subprocess
from pathlib import Path

import click
import pytest

capture_module = importlib.import_module('phonehome.capture')


class FakeClock:
    def __init__(self, interrupt_at=None):
        self.now = 0.0
        self.interrupt_at = interrupt_at

    def sleep(self, duration):
        self.now += duration
        if self.interrupt_at is not None and self.now >= self.interrupt_at:
            self.interrupt_at = None
            raise KeyboardInterrupt


class FakeTcpdump:
    def __init__(self, command, stderr, clock, *, ready_after=0.0, fail=False,
                 captured=3, dropped=0, hangs=False):
        self.command = command
        self.stderr = stderr
        self.clock = clock
        self.ready_after = ready_after
        self.fail = fail
        self.captured = captured
        self.dropped = dropped
        self.hangs = hangs
        self.returncode = None
        self.signals = []
        self.wait_timeouts = []
        self.ready = False
        self.raw = Path(command[command.index('-w') + 1])
        self.raw.write_bytes(b'pcap header'.ljust(24, b'\0'))

    def poll(self):
        if self.fail and self.returncode is None:
            self.stderr.write('tcpdump: nonexistent: No such device exists\n')
            self.stderr.flush()
            self.returncode = 1
        if not self.ready and self.clock.now >= self.ready_after and not self.fail:
            self.stderr.write('tcpdump: listening on tailscale0, link-type RAW\n')
            self.stderr.flush()
            self.ready = True
        return self.returncode

    def send_signal(self, sig):
        self.signals.append(sig)
        if self.hangs and sig != signal.SIGKILL:
            return
        if self.captured:
            self.raw.write_bytes(self.raw.read_bytes() + b'captured packet')
        # The real subprocess retains its stderr descriptor even after the
        # controller closes its own copy of the file handle.
        with open(self.stderr.name, 'a') as out:
            out.write(f'{self.captured} packets captured\n')
            out.write(f'{self.captured} packets received by filter\n')
            out.write(f'{self.dropped} packets dropped by kernel\n')
        self.returncode = 0 if sig == signal.SIGINT else -int(sig)

    def wait(self, timeout):
        self.wait_timeouts.append(timeout)
        if self.returncode is None:
            raise subprocess.TimeoutExpired(self.command, timeout)
        return self.returncode


def install_capture_fake(monkeypatch, tmp_path, **options):
    monkeypatch.chdir(tmp_path)
    clock = FakeClock(options.pop('interrupt_at', None))
    monkeypatch.setattr(capture_module.time, 'monotonic', lambda: clock.now)
    monkeypatch.setattr(capture_module.time, 'sleep', clock.sleep)
    processes = []
    dns_calls = []

    def popen(command, **kwargs):
        assert kwargs['start_new_session'] is True
        assert kwargs['env']['LC_ALL'] == 'C'
        proc = FakeTcpdump(command, kwargs['stderr'], clock, **options)
        processes.append(proc)
        return proc

    def dns(target, start, end, env):
        dns_calls.append((target, start, end))
        return {'entries': [], 'error': None}

    monkeypatch.setattr(capture_module.subprocess, 'Popen', popen)
    monkeypatch.setattr(capture_module, 'fetch_queries', dns)
    return clock, processes, dns_calls


def saved_meta(tmp_path):
    return json.loads(next(tmp_path.glob('runs/*/meta.json')).read_text())


def test_capture_duration_starts_at_readiness_and_filters_only_target(monkeypatch, tmp_path):
    clock, processes, dns_calls = install_capture_fake(monkeypatch, tmp_path, ready_after=0.8)
    folder = capture_module.capture('instagram', '192.0.2.10', 1, 'tailscale0', countdown=0)
    meta = saved_meta(tmp_path)
    assert clock.now >= 1.8
    assert meta['actual_duration_s'] == pytest.approx(1)
    assert meta['quality']['status'] == 'complete'
    assert meta['packets_captured'] == 3
    assert meta['packets_dropped_by_kernel'] == 0
    assert processes[0].command[-2:] == ['host', '192.0.2.10']
    assert processes[0].signals == [signal.SIGINT]
    assert processes[0].wait_timeouts == [capture_module.STOP_TIMEOUT_S]
    assert dns_calls[0][1].isoformat() == meta['started_at']
    assert (folder / 'dns.json').exists()


def test_capture_preserves_metadata_on_startup_error(monkeypatch, tmp_path):
    _, _, dns_calls = install_capture_fake(monkeypatch, tmp_path, fail=True)
    with pytest.raises(click.ClickException, match='startup_failed'):
        capture_module.capture('instagram', '192.0.2.10', 1, 'tailscale0', countdown=0)
    meta = saved_meta(tmp_path)
    assert meta['quality']['status'] == 'startup_failed'
    assert meta['started_at'] is None
    assert meta['tcpdump_exit_code'] == 1
    assert 'No such device' in meta['tcpdump_stats']
    assert dns_calls == []
    assert next(tmp_path.glob('runs/*/dns.json')).exists()


def test_capture_preserves_metadata_when_executable_missing(monkeypatch, tmp_path):
    install_capture_fake(monkeypatch, tmp_path)
    def missing(*args, **kwargs):
        raise FileNotFoundError('sudo')
    monkeypatch.setattr(capture_module.subprocess, 'Popen', missing)
    with pytest.raises(click.ClickException, match='startup_failed'):
        capture_module.capture('instagram', '192.0.2.10', 1, 'tailscale0', countdown=0)
    assert saved_meta(tmp_path)['capture_error'] == 'Capture could not run: FileNotFoundError'


def test_capture_interruption_marks_partial_and_stops_owned_child(monkeypatch, tmp_path):
    _, processes, _ = install_capture_fake(monkeypatch, tmp_path, interrupt_at=0.4)
    with pytest.raises(click.ClickException, match='partial'):
        capture_module.capture('instagram', '192.0.2.10', 1, 'tailscale0', countdown=0)
    meta = saved_meta(tmp_path)
    assert meta['interrupted'] is True
    assert meta['quality']['incomplete'] is True
    assert meta['actual_duration_s'] < 1
    assert processes[0].signals == [signal.SIGINT]


@pytest.mark.parametrize(('captured', 'dropped', 'status'), [(0, 0, 'empty'), (3, 2, 'lossy')])
def test_capture_marks_empty_and_lossy_runs(monkeypatch, tmp_path, captured, dropped, status):
    install_capture_fake(monkeypatch, tmp_path, captured=captured, dropped=dropped)
    with pytest.raises(click.ClickException, match=status):
        capture_module.capture('instagram', '192.0.2.10', 1, 'tailscale0', countdown=0)
    meta = saved_meta(tmp_path)
    assert meta['quality']['status'] == status
    assert meta['packets_captured'] == captured
    assert meta['packets_dropped_by_kernel'] == dropped


def test_capture_shutdown_escalates_with_bounded_waits(monkeypatch, tmp_path):
    _, processes, _ = install_capture_fake(monkeypatch, tmp_path, hangs=True)
    with pytest.raises(click.ClickException, match='partial'):
        capture_module.capture('instagram', '192.0.2.10', 1, 'tailscale0', countdown=0)
    assert processes[0].signals == [signal.SIGINT, signal.SIGTERM, signal.SIGKILL]
    assert processes[0].wait_timeouts == [capture_module.STOP_TIMEOUT_S] * 3
    assert saved_meta(tmp_path)['quality']['forced_shutdown'] is True


def test_capture_readiness_timeout_is_bounded(monkeypatch, tmp_path):
    clock, _, _ = install_capture_fake(monkeypatch, tmp_path, ready_after=1000)
    with pytest.raises(click.ClickException, match='startup_failed'):
        capture_module.capture('instagram', '192.0.2.10', 1, 'tailscale0', countdown=0)
    assert clock.now < capture_module.STARTUP_TIMEOUT_S + 0.1
    assert 'startup deadline' in saved_meta(tmp_path)['capture_error']


def test_capture_refuses_existing_run_without_touching_raw(monkeypatch, tmp_path):
    install_capture_fake(monkeypatch, tmp_path)
    fixed_now = dt.datetime(2026, 11, 7, 12, tzinfo=dt.timezone.utc)

    class FrozenDatetime(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now.astimezone(tz)

    monkeypatch.setattr(capture_module.dt, 'datetime', FrozenDatetime)
    stamp = fixed_now.astimezone()
    folder = tmp_path / 'runs' / f'{stamp:%Y%m%d-%H%M%S}-instagram'
    folder.mkdir(parents=True)
    raw = folder / 'raw.pcap'
    raw.write_bytes(b'original evidence')
    with pytest.raises(click.ClickException, match='Run already exists'):
        capture_module.capture('instagram', '192.0.2.10', 1, 'tailscale0', countdown=0)
    assert raw.read_bytes() == b'original evidence'
