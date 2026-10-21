"""Load research inputs only when their APK hashes match the checked-in discovery report."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verified_apk(app, apk_name):
    app_root = ROOT / 'apps' / app
    report = json.loads((app_root / 'evidence/static-analysis.json').read_text())
    expected = {item['name']: item['sha256'] for item in report['inputs']}
    apk = app_root / 'apks' / apk_name
    if hashlib.sha256(apk.read_bytes()).hexdigest() != expected[apk_name]:
        raise ValueError(f'{app}: APK differs from the analyzed snapshot; generate and review discovery first')
    return apk


def extract_member(app, apk_name, member, local_name):
    apk = verified_apk(app, apk_name)
    destination = ROOT / 'apps' / app / 'runs/static-deep' / local_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(apk) as archive:
        data = archive.read(member)
    destination.write_bytes(data)
    return destination
