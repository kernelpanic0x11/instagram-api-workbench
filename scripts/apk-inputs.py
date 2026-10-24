#!/usr/bin/env python3
"""Keep verified APK snapshots outside a checkout and restore them without a phone."""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {'instagram': 'com.instagram.android', 'snapchat': 'com.snapchat.android',
            'discord': 'com.discord', 'tiktok': 'com.zhiliaoapp.musically', 'roblox': 'com.roblox.client'}


def default_archive():
    if os.environ.get('APK_ARCHIVE_DIR'):
        return Path(os.environ['APK_ARCHIVE_DIR']).expanduser()
    if sys.platform == 'darwin':
        base = Path.home() / 'Library/Application Support'
    elif os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
    else:
        base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    return base / 'mobile-api-workbench/apks'


def digest(file):
    checksum = hashlib.sha256()
    with file.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def snapshot_id(files):
    identity = [{key: entry[key] for key in ('name', 'sha256', 'bytes')} for entry in files]
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_manifest(manifest):
    files = manifest['files']
    names = [entry['name'] for entry in files]
    if 'base.apk' not in names or len(set(names)) != len(names):
        raise ValueError('Snapshot must contain base.apk and unique APK filenames')
    for entry in files:
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.apk', entry['name']):
            raise ValueError('Unsafe snapshot filename')
        if not re.fullmatch(r'[a-f0-9]{64}', entry['sha256']) or not isinstance(entry['bytes'], int) or entry['bytes'] <= 0:
            raise ValueError('Invalid snapshot file metadata')
    if manifest['snapshot'] != snapshot_id(files):
        raise ValueError('Snapshot manifest identity mismatch')


def verify_snapshot(directory, manifest):
    validate_manifest(manifest)
    for entry in manifest['files']:
        file = directory / entry['name']
        if file.is_symlink() or file.stat().st_size != entry['bytes'] or digest(file) != entry['sha256']:
            raise ValueError('Snapshot bytes failed verification: ' + entry['name'])


def archive_inputs(app, source, archive_root, version=None):
    inputs = sorted(source.glob('*.apk'))
    if not inputs:
        raise ValueError('No APKs found in source directory')
    expected = None
    receipt = source / 'acquisition.json'
    if receipt.exists():
        acquired = json.loads(receipt.read_text())
        if acquired['package'] != PACKAGES[app]:
            raise ValueError('Acquisition package differs from the selected app')
        expected = {entry['name']: entry['sha256'] for entry in acquired['files']}
        if set(expected) != {file.name for file in inputs}:
            raise ValueError('APK set differs from acquisition receipt')
    files = []
    for file in inputs:
        if file.is_symlink():
            raise ValueError('Provide ordinary APK files, not symlinks')
        with zipfile.ZipFile(file) as archive:
            if archive.testzip():
                raise ValueError('APK ZIP integrity failed: ' + file.name)
        checksum = digest(file)
        if expected is not None and checksum != expected[file.name]:
            raise ValueError('APK differs from acquisition receipt: ' + file.name)
        files.append({'name': file.name, 'sha256': checksum, 'bytes': file.stat().st_size})
    manifest = {'schema_version': 1, 'app': app, 'package': PACKAGES[app], 'version': version,
                'snapshot': snapshot_id(files), 'files': files,
                'note': 'Local APK inputs only. No source paths, device IDs, credentials or account storage.'}
    validate_manifest(manifest)
    parent = archive_root / app
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = parent / manifest['snapshot']
    if destination.exists():
        existing = json.loads((destination / 'snapshot.json').read_text())
        verify_snapshot(destination, existing)
        return existing
    with tempfile.TemporaryDirectory(prefix='.archive-', dir=parent) as temporary:
        staged = Path(temporary)
        for entry in files:
            target = staged / entry['name']
            shutil.copyfile(source / entry['name'], target)
            target.chmod(0o600)
        (staged / 'snapshot.json').write_text(json.dumps(manifest, indent=2) + '\n')
        (staged / 'snapshot.json').chmod(0o600)
        verify_snapshot(staged, manifest)
        staged.rename(destination)
    return manifest


def restore_inputs(app, snapshot, destination, archive_root):
    if not re.fullmatch(r'[a-f0-9]{64}', snapshot):
        raise ValueError('Select a full snapshot ID from the list command')
    source = archive_root / app / snapshot
    manifest = json.loads((source / 'snapshot.json').read_text())
    if manifest['app'] != app or manifest['package'] != PACKAGES[app] or manifest['snapshot'] != snapshot:
        raise ValueError('Snapshot app or identity mismatch')
    verify_snapshot(source, manifest)
    if destination.exists():
        verify_snapshot(destination, manifest)
        return manifest
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.restore-', dir=destination.parent) as temporary:
        staged = Path(temporary)
        for entry in manifest['files']:
            target = staged / entry['name']
            shutil.copyfile(source / entry['name'], target)
            target.chmod(0o600)
        acquisition = {'package': manifest['package'], 'files': manifest['files'],
                       'snapshot': snapshot, 'note': 'Restored from a verified local archive; no device access performed.'}
        (staged / 'acquisition.json').write_text(json.dumps(acquisition, indent=2) + '\n')
        (staged / 'acquisition.json').chmod(0o600)
        verify_snapshot(staged, manifest)
        staged.rename(destination)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-root', type=Path, default=default_archive())
    commands = parser.add_subparsers(dest='command', required=True)
    archive = commands.add_parser('archive', help='Copy APKs into a verified persistent snapshot')
    archive.add_argument('app', choices=PACKAGES)
    archive.add_argument('--source', type=Path)
    archive.add_argument('--version')
    listing = commands.add_parser('list', help='List snapshots without printing identifying filesystem paths')
    listing.add_argument('app', choices=PACKAGES)
    restore = commands.add_parser('restore', help='Restore a verified snapshot into an empty checkout input directory')
    restore.add_argument('app', choices=PACKAGES)
    restore.add_argument('--snapshot', required=True)
    restore.add_argument('--destination', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'list':
            for file in sorted((args.archive_root / args.app).glob('*/snapshot.json')):
                manifest = json.loads(file.read_text())
                validate_manifest(manifest)
                print(json.dumps({'app': args.app, 'snapshot': manifest['snapshot'], 'version': manifest['version'], 'apks': len(manifest['files'])}))
            return
        if args.command == 'archive':
            manifest = archive_inputs(args.app, args.source or REPOSITORY_ROOT / 'apps' / args.app / 'apks', args.archive_root, args.version)
        else:
            manifest = restore_inputs(args.app, args.snapshot, args.destination or REPOSITORY_ROOT / 'apps' / args.app / 'apks', args.archive_root)
        print(json.dumps({'action': args.command, 'app': args.app, 'snapshot': manifest['snapshot'], 'apks': len(manifest['files']), 'verified': True}))
    except (ValueError, OSError, KeyError, zipfile.BadZipFile):
        raise SystemExit('Input snapshot failed verification or could not be accessed. No existing snapshot was overwritten.')


if __name__ == '__main__':
    main()
