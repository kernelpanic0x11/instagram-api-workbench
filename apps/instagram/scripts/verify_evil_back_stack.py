#!/usr/bin/env python3
"""Verify that Back from Evil Instagram's profile stays inside the clone."""
import argparse
import re
import subprocess
import time


PACKAGE = 'com.instagram.android.inspect'
LAUNCHER = f'{PACKAGE}/com.instagram.android.activity.MainTabActivity'


def adb(*args, check=True):
    result = subprocess.run(
        ['adb', *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return result.stdout


def top_resumed_activity():
    output = adb('shell', 'dumpsys', 'activity', 'activities')
    match = re.search(r'topResumedActivity=ActivityRecord\{.*? ([^ ]+) t\d+\}', output)
    if not match:
        raise AssertionError('Android did not report a top resumed activity')
    return match.group(1)


def require_unlocked_phone():
    adb('shell', 'input', 'keyevent', 'KEYCODE_WAKEUP')
    adb('shell', 'wm', 'dismiss-keyguard')
    time.sleep(1)
    window_state = adb('shell', 'dumpsys', 'window')
    focus = re.search(r'^\s*mCurrentFocus=(.*)$', window_state, re.MULTILINE)
    focus_value = focus.group(1) if focus else ''
    if 'Bouncer' in focus_value or 'Keyguard' in focus_value or 'mDreamingLockscreen=true' in window_state:
        raise SystemExit('unlock the phone before running the Back verifier')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempts', type=int, default=3)
    args = parser.parse_args()

    if args.attempts < 1:
        parser.error('--attempts must be at least 1')
    if '\tdevice' not in adb('devices'):
        raise SystemExit('no authorized ADB device is connected')
    require_unlocked_phone()

    for attempt in range(1, args.attempts + 1):
        adb('shell', 'am', 'force-stop', PACKAGE)
        adb('logcat', '-c')
        adb('shell', 'am', 'start', '-n', LAUNCHER)
        time.sleep(4)
        before = top_resumed_activity()
        if not before.startswith(PACKAGE + '/'):
            raise AssertionError(f'attempt {attempt}: clone was not foreground before Back: {before}')

        adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        time.sleep(1)
        after = top_resumed_activity()
        if not after.startswith(PACKAGE + '/'):
            raise AssertionError(f'attempt {attempt}: Back left the clone: {after}')

        logcat = adb('logcat', '-d', '-v', 'brief')
        fatal_for_clone = 'FATAL EXCEPTION' in logcat and f'Process: {PACKAGE}' in logcat
        if fatal_for_clone:
            raise AssertionError(f'attempt {attempt}: Android logged a fatal clone exception')
        print(f'attempt {attempt}: PASS ({before} -> {after})')


if __name__ == '__main__':
    main()
