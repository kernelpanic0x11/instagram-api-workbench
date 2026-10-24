#!/usr/bin/env python3
"""Extract pinned instruction evidence for one reviewed keyword-settings contract."""
import argparse
import importlib.util
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('shared', DIRECTORY / 'trace-shared-contracts.py')
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
shared.SELECTORS = {
    ('LX/09eD;', 'A00', '(Lcom/instagram/common/session/UserSession;LX/09eD;LX/0Pmx;)Ljava/lang/Object;'),
    ('LX/0djX;', 'unsafeParseFromJson', '(LX/04s3;)Ljava/lang/Object;'),
    ('LX/01yt;', 'A0B', '(LX/04s3;)Ljava/util/ArrayList;'),
    ('LX/01yt;', 'A07', '(LX/04s3;)Ljava/lang/String;'),
    ('LX/0025;', 'A0H', '(LX/04s3;)Ljava/lang/Integer;'),
    # Required by the shared collector's reviewed transport/token assertions.
    ('LX/04x6;', 'A02', '()LX/02uC;'),
    ('LX/01yl;', '<clinit>', '()V'),
    ('LX/02sE;', 'call', '()Ljava/lang/Object;'),
    ('LX/041Z;', 'A00', '(LX/01Jp;LX/05Dd;LX/0Ddm;Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Object;'),
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--endpoint', choices=['comment', 'post'], default='comment')
    args = parser.parse_args()
    if args.endpoint == 'post':
        shared.SELECTORS.remove(('LX/09eD;', 'A00', '(Lcom/instagram/common/session/UserSession;LX/09eD;LX/0Pmx;)Ljava/lang/Object;'))
        shared.SELECTORS.update({
            ('LX/0HVZ;', 'onViewCreated', '(Landroid/view/View;Landroid/os/Bundle;)V'),
            ('LX/0Qvj;', 'Cya', '(ZLX/0Pmx;)Ljava/lang/Object;'),
            ('LX/0221;', 'A0K', '(LX/02rr;LX/0Wvm;Lcom/instagram/common/session/UserSession;)LX/02sB;'),
        })
    evidence = shared.collect(DIRECTORY.parents[1] / 'apks/base.apk')
    evidence.pop('rules')  # Shared rules are published separately, not inferred here.
    (DIRECTORY / (args.endpoint + '-keywords-evidence.json')).write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({'reviewed_methods': len(evidence['methods'])}))
