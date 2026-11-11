#!/usr/bin/env python3
import unittest
from pathlib import Path


SOURCE = Path(__file__).with_name('EvilLaunchActivity.java')


class EvilLaunchActivityTest(unittest.TestCase):
    def test_profile_launch_keeps_instagram_main_in_back_stack(self):
        source = SOURCE.read_text()
        profile_branch = source[source.index('if (!username.isEmpty()) {'):source.index('return;', source.index('if (!username.isEmpty()) {'))]

        self.assertIn('com.instagram.mainactivity.InstagramMainActivity', profile_branch)
        self.assertIn('com.instagram.url.UrlHandlerActivity', profile_branch)
        self.assertIn('startActivities(new Intent[] {main, profile});', profile_branch)
        self.assertNotIn('startActivity(profile);', profile_branch)

    def test_profile_fire_overlay_is_scoped_and_does_not_capture_input(self):
        source = SOURCE.read_text()

        self.assertIn('com.instagram.url.UrlHandlerActivity', source)
        self.assertIn('evil_fire_overlay.png', source)
        self.assertIn('fire.setClickable(false);', source)
        self.assertIn('fire.setFocusable(false);', source)
        self.assertIn('IMPORTANT_FOR_ACCESSIBILITY_NO', source)
        self.assertIn('decor.findViewWithTag(FIRE_OVERLAY_TAG)', source)

    def test_fire_overlay_animates_and_releases_its_animator(self):
        source = SOURCE.read_text()

        self.assertIn('ValueAnimator.INFINITE', source)
        self.assertIn('setAlpha(flicker);', source)
        self.assertIn('setScaleY(', source)
        self.assertIn('setTranslationY(', source)
        self.assertIn('protected void onDetachedFromWindow()', source)
        self.assertIn('flameAnimator.cancel();', source)

    def test_real_profile_views_receive_terminal_theme(self):
        source = SOURCE.read_text()

        self.assertIn('styleProfileViewTree(activity);', source)
        self.assertIn('view instanceof TextView', source)
        self.assertIn('styleView(group.getChildAt(index), density);', source)
        self.assertIn('TERMINAL_GREEN', source)
        self.assertIn('MR_ROBOT_RED', source)
        self.assertIn('Typeface.MONOSPACE', source)
        self.assertIn('terminalButton.setStroke', source)
        self.assertIn('buttonSurface.setBackground(terminalButton);', source)
        self.assertIn('targetProfileUsername = username;', source)


if __name__ == '__main__':
    unittest.main()
