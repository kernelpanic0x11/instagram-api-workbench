"""Capture a single device and collect matching AdGuard query records."""
import datetime as dt
import ipaddress
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

import click
import requests


def read_env(path=Path('.env')):
    values = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                values[key.strip()] = value.strip().strip('"\'')
    return {**values, **os.environ}


def iso(now):
    return now.astimezone(dt.timezone.utc).isoformat()


def fetch_queries(target, start, end, env):
    base = env.get('ADGUARD_URL', 'http://127.0.0.1').rstrip('/')
    username, password = env.get('ADGUARD_USERNAME'), env.get('ADGUARD_PASSWORD')
    if not username or not password:
        return {'entries': [], 'error': 'AdGuard credentials are not configured'}
    entries, older_than = [], None
    try:
        for _ in range(100):
            params = {'limit': 500, 'search': target}
            if older_than:
                params['older_than'] = older_than
            response = requests.get(base + '/control/querylog', params=params,
                                    auth=(username, password), timeout=10)
            response.raise_for_status()
            data = response.json()
            page = data.get('data') or []
            for item in page:
                stamp = dt.datetime.fromisoformat(item['time'].replace('Z', '+00:00'))
                if start <= stamp <= end and item.get('client') == target:
                    entries.append(item)
            oldest = data.get('oldest')
            # Filtered searches can return an empty page with a continuation
            # cursor after reaching AdGuard's per-request file scan limit.
            if not oldest or oldest == older_than:
                break
            if dt.datetime.fromisoformat(oldest.replace('Z', '+00:00')) < start:
                break
            older_than = oldest
        else:
            return {'entries': entries, 'error': 'AdGuard pagination limit reached'}
        return {'entries': entries, 'error': None}
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        return {'entries': entries, 'error': f'AdGuard query failed: {type(exc).__name__}'}


STARTUP_TIMEOUT_S = 10
STOP_TIMEOUT_S = 5


def _write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def _stop_capture(proc):
    """Stop only our subprocess, with bounded graceful and forced waits.

    The privileged GNU timeout wrapper also bounds the tcpdump child lifetime
    if sudo itself becomes unresponsive or the controller is killed.
    """
    forced = False
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGKILL):
        if proc.poll() is not None:
            return forced, None
        if sig != signal.SIGINT:
            forced = True
        try:
            proc.send_signal(sig)
            proc.wait(timeout=STOP_TIMEOUT_S)
            return forced, None
        except subprocess.TimeoutExpired:
            continue
        except KeyboardInterrupt:
            # A second Ctrl-C must not discard metadata or bypass cleanup.
            forced = True
            continue
        except ProcessLookupError:
            return forced, None
        except OSError as exc:
            return True, f'Capture shutdown failed: {type(exc).__name__}'
    return True, 'Capture subprocess did not exit within the shutdown deadline'


def _packet_stats(stderr):
    labels = {'packets_captured': 'captured',
              'packets_received_by_filter': 'received by filter',
              'packets_dropped_by_kernel': 'dropped by kernel'}
    stats = {}
    for key, label in labels.items():
        matches = re.findall(rf'(?m)^(\d+) packets? {label}\s*$', stderr)
        stats[key] = int(matches[-1]) if matches else None
    return stats


def capture(app, target, duration, iface, countdown=10):
    target = str(ipaddress.ip_address(target))
    if duration <= 0:
        raise click.ClickException('Duration must be positive.')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', app):
        raise click.ClickException('App name must contain only letters, numbers, underscores or hyphens.')
    if not re.fullmatch(r'[A-Za-z0-9_.:-]+', iface):
        raise click.ClickException('Invalid interface name.')
    for left in range(countdown, 0, -1):
        click.echo(f'Capture starts in {left} seconds...', err=True)
        time.sleep(1)
    launched = dt.datetime.now(dt.timezone.utc)
    folder = Path('runs') / f'{launched.astimezone():%Y%m%d-%H%M%S}-{app.lower()}'
    try:
        folder.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise click.ClickException(f'Run already exists: {folder}; no files were changed.') from exc
    raw = folder / 'raw.pcap'
    log = folder / 'tcpdump.log'
    # timeout is a privileged backstop, not the requested capture timer.  The
    # requested timer below starts only after tcpdump reports it is listening.
    command = ['sudo', '-n', 'timeout', '--signal=INT', '--kill-after=3s',
               f'{duration + STARTUP_TIMEOUT_S + 5}s', 'tcpdump', '-U', '-n',
               '-i', iface, '-w', str(raw), 'host', target]
    meta = {'app': app, 'phone_ip': target, 'duration_s': duration, 'iface': iface,
            'launch_requested_at': iso(launched), 'started_at': None, 'ended_at': None,
            'interrupted': False, 'tcpdump_exit_code': None, 'tcpdump_stats': '',
            'dns_error': None, 'command': command, 'quality': {'status': 'starting'}}
    _write_json(folder / 'meta.json', meta)
    proc = None
    started = None
    start_clock = None
    ended = None
    actual_duration = 0.0
    completed = False
    forced = False
    error = None
    try:
        # A file avoids pipe backpressure or waiting forever for inherited pipe
        # descriptors in sudo's descendants.  LC_ALL stabilizes readiness/stats.
        with log.open('x') as stderr_file:
            proc = subprocess.Popen(command, stdout=subprocess.DEVNULL,
                                    stderr=stderr_file, start_new_session=True,
                                    env={**os.environ, 'LC_ALL': 'C'})
            startup_deadline = time.monotonic() + STARTUP_TIMEOUT_S
            while True:
                if 'listening on ' in log.read_text(errors='replace'):
                    started = dt.datetime.now(dt.timezone.utc)
                    start_clock = time.monotonic()
                    break
                if proc.poll() is not None:
                    error = 'tcpdump exited before reporting readiness'
                    break
                if time.monotonic() >= startup_deadline:
                    error = 'tcpdump did not report readiness before the startup deadline'
                    break
                time.sleep(0.05)
            if started is not None:
                deadline = start_clock + duration
                while proc.poll() is None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        completed = True
                        break
                    time.sleep(min(0.1, remaining))
                if not completed:
                    error = 'tcpdump exited before the requested capture window ended'
    except KeyboardInterrupt:
        meta['interrupted'] = True
        error = 'Capture interrupted'
    except OSError as exc:
        error = f'Capture could not run: {type(exc).__name__}'
    finally:
        ended = dt.datetime.now(dt.timezone.utc)
        if start_clock is not None:
            actual_duration = time.monotonic() - start_clock
        if proc is not None:
            forced, stop_error = _stop_capture(proc)
            if stop_error:
                error = stop_error

    stderr = log.read_text(errors='replace') if log.exists() else ''
    stats = _packet_stats(stderr)
    pcap_bytes = raw.stat().st_size if raw.exists() else 0
    incomplete = not completed or forced or bool(error) or (proc is not None and proc.returncode != 0)
    empty = stats['packets_captured'] == 0 or pcap_bytes <= 24
    lossy = (stats['packets_dropped_by_kernel'] or 0) > 0
    stats_available = all(value is not None for value in stats.values())
    if started is None:
        status = 'startup_failed'
    elif incomplete:
        status = 'partial'
    elif empty:
        status = 'empty'
    elif lossy:
        status = 'lossy'
    elif not stats_available:
        status = 'unverified'
    else:
        status = 'complete'
    meta.update(started_at=iso(started) if started else None, ended_at=iso(ended),
                actual_duration_s=actual_duration, tcpdump_exit_code=proc.returncode if proc else None,
                tcpdump_stats=stderr, capture_error=error, pcap_bytes=pcap_bytes, **stats,
                quality={'status': status, 'incomplete': incomplete, 'empty': empty,
                         'lossy': lossy, 'stats_available': stats_available,
                         'forced_shutdown': forced})
    # Persist capture evidence before the optional network lookup, including
    # failed startups and interrupts, so another interrupt cannot erase it.
    _write_json(folder / 'meta.json', meta)
    dns = {'entries': [], 'error': 'Capture did not start'}
    try:
        if started is not None:
            dns = fetch_queries(target, started, ended, read_env())
    except KeyboardInterrupt:
        dns = {'entries': [], 'error': 'DNS retrieval interrupted'}
    _write_json(folder / 'dns.json', dns)
    meta['dns_error'] = dns['error']
    _write_json(folder / 'meta.json', meta)
    click.echo(f'Capture saved to {folder} ({status})')
    if dns['error']:
        click.echo(f"Warning: {dns['error']}", err=True)
    if status != 'complete':
        raise click.ClickException(f'Capture status: {status}; files and metadata were preserved in {folder}.')
    return folder
