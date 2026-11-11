package com.evilinstagram;

import android.animation.ObjectAnimator;
import android.animation.ValueAnimator;
import android.app.Activity;
import android.app.Application;
import android.content.Intent;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewParent;
import android.view.Window;
import android.view.animation.DecelerateInterpolator;
import android.view.animation.LinearInterpolator;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.InputStreamReader;

public final class EvilLaunchActivity extends Activity {
    private static final long LAUNCH_DELAY_MS = 1850;
    private static final String FIRE_OVERLAY_TAG = "evil_instagram_fire_overlay";
    private static final int MR_ROBOT_RED = Color.rgb(255, 38, 58);
    private static final int TERMINAL_GREEN = Color.rgb(54, 255, 115);
    private static final int TERMINAL_TEXT = Color.rgb(218, 255, 226);
    private static final int TERMINAL_BLACK = Color.rgb(3, 7, 5);
    private static boolean fireCallbacksRegistered;
    private static String targetProfileUsername = "";

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        registerFireOverlay();
        Window window = getWindow();
        window.setStatusBarColor(Color.BLACK);
        window.setNavigationBarColor(Color.BLACK);

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);

        GlitchView glitch = new GlitchView(this);
        root.addView(glitch, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
        ));

        int iconSize = dp(198);
        ImageView icon = new ImageView(this);
        try {
            icon.setImageBitmap(BitmapFactory.decodeStream(getAssets().open("evil_emblem.png")));
        } catch (Exception ignored) {
            Drawable drawable = getApplicationInfo().loadIcon(getPackageManager());
            icon.setImageDrawable(drawable);
        }
        icon.setAlpha(0f);
        icon.setScaleX(0.78f);
        icon.setScaleY(0.78f);
        FrameLayout.LayoutParams iconParams = new FrameLayout.LayoutParams(iconSize, iconSize, Gravity.CENTER);
        root.addView(icon, iconParams);

        RingView ring = new RingView(this);
        FrameLayout.LayoutParams ringParams = new FrameLayout.LayoutParams(dp(218), dp(218), Gravity.CENTER);
        root.addView(ring, ringParams);

        StatusView status = new StatusView(this, "LOCATION // DENIED", 15f, Color.rgb(255, 36, 36));
        status.setAlpha(0f);
        FrameLayout.LayoutParams statusParams = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                dp(48),
                Gravity.CENTER
        );
        statusParams.topMargin = dp(260);
        root.addView(status, statusParams);

        StatusView title = new StatusView(this, "E V I L   I N S T A G R A M", 11f, Color.rgb(148, 148, 148));
        title.setAlpha(0f);
        FrameLayout.LayoutParams titleParams = new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, dp(40), Gravity.TOP
        );
        titleParams.topMargin = dp(72);
        root.addView(title, titleParams);
        setContentView(root);

        icon.animate()
                .alpha(1f)
                .scaleX(1f)
                .scaleY(1f)
                .setDuration(620)
                .setInterpolator(new DecelerateInterpolator())
                .start();

        ObjectAnimator.ofFloat(icon, View.TRANSLATION_X, 0f, -dp(7), dp(5), -dp(2), 0f)
                .setDuration(720)
                .start();

        ValueAnimator sweep = ValueAnimator.ofFloat(0f, 1f);
        sweep.setStartDelay(240);
        sweep.setDuration(900);
        sweep.setInterpolator(new DecelerateInterpolator());
        sweep.addUpdateListener(new ValueAnimator.AnimatorUpdateListener() {
            @Override
            public void onAnimationUpdate(ValueAnimator animation) {
                ring.setProgress((Float) animation.getAnimatedValue());
            }
        });
        sweep.start();

        glitch.start();
        title.animate().alpha(0.8f).setStartDelay(180).setDuration(220).start();
        status.animate().alpha(1f).setStartDelay(470).setDuration(180).start();
        root.postDelayed(new Runnable() {
            @Override
            public void run() {
                openProfile();
            }
        }, LAUNCH_DELAY_MS);
    }

    /** Keep the effect process-local: no overlay permission and no touch interception. */
    private void registerFireOverlay() {
        if (fireCallbacksRegistered) {
            return;
        }
        fireCallbacksRegistered = true;
        getApplication().registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks() {
            @Override
            public void onActivityResumed(final Activity activity) {
                if (!"com.instagram.url.UrlHandlerActivity".equals(activity.getClass().getName())) {
                    return;
                }
                activity.getWindow().getDecorView().postDelayed(new Runnable() {
                    @Override
                    public void run() {
                        addFireOverlay(activity);
                        styleProfileViewTree(activity);
                    }
                }, 350);
                activity.getWindow().getDecorView().postDelayed(new Runnable() {
                    @Override
                    public void run() {
                        styleProfileViewTree(activity);
                    }
                }, 1300);
                activity.getWindow().getDecorView().postDelayed(new Runnable() {
                    @Override
                    public void run() {
                        styleProfileViewTree(activity);
                    }
                }, 2600);
            }

            @Override public void onActivityCreated(Activity activity, Bundle state) {}
            @Override public void onActivityStarted(Activity activity) {}
            @Override public void onActivityPaused(Activity activity) {}
            @Override public void onActivityStopped(Activity activity) {}
            @Override public void onActivitySaveInstanceState(Activity activity, Bundle state) {}
            @Override public void onActivityDestroyed(Activity activity) {}
        });
    }

    /** Restyle Instagram's real profile views; these edits scroll with the page. */
    private static void styleProfileViewTree(Activity activity) {
        if (activity.isFinishing() || activity.isDestroyed()) {
            return;
        }
        View decor = activity.getWindow().getDecorView();
        decor.setBackgroundColor(TERMINAL_BLACK);
        styleView(decor, activity.getResources().getDisplayMetrics().density);
    }

    private static void styleView(View view, float density) {
        if (view instanceof FireOverlayView) {
            return;
        }
        if (view instanceof TextView) {
            styleTextView((TextView) view, density);
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int index = 0; index < group.getChildCount(); index++) {
                styleView(group.getChildAt(index), density);
            }
        }
    }

    private static void styleTextView(TextView textView, float density) {
        CharSequence value = textView.getText();
        String text = value == null ? "" : value.toString().trim();
        if (text.isEmpty()) {
            return;
        }
        String lower = text.toLowerCase(java.util.Locale.US);
        boolean metric = text.matches("[0-9]+(?:\\.[0-9]+)?[KMB]?")
                || lower.equals("posts")
                || lower.equals("followers")
                || lower.equals("following");
        boolean action = lower.equals("edit profile")
                || lower.equals("share profile")
                || lower.equals("add");
        boolean profileHandle = !targetProfileUsername.isEmpty()
                && lower.equals(targetProfileUsername.toLowerCase(java.util.Locale.US));
        boolean heading = profileHandle
                || lower.contains("dashboard")
                || (!metric && textView.getTextSize() / density >= 22f);

        int color = metric ? TERMINAL_GREEN : heading || action ? MR_ROBOT_RED : TERMINAL_TEXT;
        textView.setTextColor(color);
        textView.setShadowLayer(metric ? 5f * density : 2f * density, 0f, 0f, color);

        if (metric || heading || action) {
            textView.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));
            textView.setLetterSpacing(metric ? 0.04f : 0.02f);
        }
        if (action) {
            int horizontal = textView.getPaddingLeft();
            int top = textView.getPaddingTop();
            int right = textView.getPaddingRight();
            int bottom = textView.getPaddingBottom();
            GradientDrawable terminalButton = new GradientDrawable();
            terminalButton.setColor(TERMINAL_BLACK);
            terminalButton.setCornerRadius(11f * density);
            terminalButton.setStroke(Math.max(2, Math.round(1.5f * density)), MR_ROBOT_RED);
            ViewParent parent = textView.getParent();
            View buttonSurface = parent instanceof View ? (View) parent : textView;
            buttonSurface.setBackground(terminalButton);
            textView.setPadding(horizontal, top, right, bottom);
        }
    }

    private static void addFireOverlay(Activity activity) {
        if (activity.isFinishing() || activity.isDestroyed()) {
            return;
        }
        View decor = activity.getWindow().getDecorView();
        if (!(decor instanceof ViewGroup) || decor.findViewWithTag(FIRE_OVERLAY_TAG) != null) {
            return;
        }
        try {
            FireOverlayView fire = new FireOverlayView(activity);
            fire.setTag(FIRE_OVERLAY_TAG);
            fire.setImageBitmap(BitmapFactory.decodeStream(activity.getAssets().open("evil_fire_overlay.png")));
            fire.setScaleType(ImageView.ScaleType.FIT_XY);
            fire.setClickable(false);
            fire.setFocusable(false);
            fire.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
            ((ViewGroup) decor).addView(fire, new ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
            ));
        } catch (Exception ignored) {
            // Profile launch must continue even if the optional visual asset is unavailable.
        }
    }

    private static final class FireOverlayView extends ImageView {
        private final float density;
        private ValueAnimator flameAnimator;

        FireOverlayView(Activity activity) {
            super(activity);
            density = activity.getResources().getDisplayMetrics().density;
        }

        @Override
        protected void onAttachedToWindow() {
            super.onAttachedToWindow();
            post(new Runnable() {
                @Override
                public void run() {
                    setPivotX(getWidth() / 2f);
                    setPivotY(getHeight());
                    startFlameAnimation();
                }
            });
        }

        private void startFlameAnimation() {
            if (flameAnimator != null) {
                flameAnimator.cancel();
            }
            flameAnimator = ValueAnimator.ofFloat(0f, 1f);
            flameAnimator.setDuration(3600);
            flameAnimator.setRepeatCount(ValueAnimator.INFINITE);
            flameAnimator.setInterpolator(new LinearInterpolator());
            flameAnimator.addUpdateListener(new ValueAnimator.AnimatorUpdateListener() {
                @Override
                public void onAnimationUpdate(ValueAnimator animation) {
                    float phase = (Float) animation.getAnimatedValue() * (float) (Math.PI * 2.0);
                    float flicker = 0.78f
                            + 0.065f * (float) Math.sin(phase * 3.0f)
                            + 0.025f * (float) Math.sin(phase * 11.0f);
                    setAlpha(flicker);
                    setScaleX(1.012f + 0.008f * (float) Math.sin(phase * 1.2f));
                    setScaleY(1.020f + 0.018f * (float) Math.sin(phase * 1.7f));
                    setTranslationY(density * 2.5f * (float) Math.sin(phase * 2.1f));
                }
            });
            flameAnimator.start();
        }

        @Override
        protected void onDetachedFromWindow() {
            if (flameAnimator != null) {
                flameAnimator.cancel();
                flameAnimator = null;
            }
            super.onDetachedFromWindow();
        }
    }

    private void openProfile() {
        final String username = readProfileUsername();
        targetProfileUsername = username;
        if (!username.isEmpty()) {
            Intent main = new Intent(Intent.ACTION_MAIN);
            main.setClassName(getPackageName(), "com.instagram.mainactivity.InstagramMainActivity");
            main.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NO_ANIMATION);

            Intent profile = new Intent(Intent.ACTION_VIEW);
            profile.setData(Uri.parse("instagram://user?username=" + Uri.encode(username)));
            profile.setClassName(getPackageName(), "com.instagram.url.UrlHandlerActivity");
            profile.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
            startActivities(new Intent[] {main, profile});
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
            finish();
            return;
        }
        Intent main = new Intent(Intent.ACTION_MAIN);
        main.setClassName(getPackageName(), "com.instagram.mainactivity.InstagramMainActivity");
        main.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        startActivity(main);
        overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
        finish();
    }

    private String readProfileUsername() {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(getAssets().open("evil_profile")))) {
            String value = reader.readLine();
            return value == null ? "" : value.trim();
        } catch (Exception ignored) {
            return "";
        }
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private static final class RingView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private float progress;

        RingView(Activity activity) {
            super(activity);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(activity.getResources().getDisplayMetrics().density * 3f);
            paint.setStrokeCap(Paint.Cap.ROUND);
            paint.setColor(Color.rgb(255, 24, 24));
            setAlpha(0.9f);
        }

        void setProgress(float value) {
            progress = value;
            invalidate();
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            float inset = paint.getStrokeWidth() / 2f;
            RectF bounds = new RectF(inset, inset, getWidth() - inset, getHeight() - inset);
            canvas.drawArc(bounds, -90f, 360f * progress, false, paint);
        }
    }

    /** Draw directly so Instagram's unresolved TextView theme attributes cannot crash startup. */
    private static final class StatusView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final String text;

        StatusView(Activity activity, String text, float textSize, int color) {
            super(activity);
            this.text = text;
            paint.setColor(color);
            paint.setTextAlign(Paint.Align.CENTER);
            paint.setTextSize(activity.getResources().getDisplayMetrics().scaledDensity * textSize);
            paint.setLetterSpacing(0.08f);
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            Paint.FontMetrics metrics = paint.getFontMetrics();
            float baseline = (getHeight() - metrics.bottom - metrics.top) / 2f;
            canvas.drawText(text, getWidth() / 2f, baseline, paint);
        }
    }

    private static final class GlitchView extends View {
        private final Paint paint = new Paint();
        private float phase;

        GlitchView(Activity activity) {
            super(activity);
            paint.setColor(Color.rgb(255, 0, 24));
        }

        void start() {
            ValueAnimator animator = ValueAnimator.ofFloat(0f, 1f);
            animator.setDuration(1050);
            animator.addUpdateListener(new ValueAnimator.AnimatorUpdateListener() {
                @Override
                public void onAnimationUpdate(ValueAnimator animation) {
                    phase = (Float) animation.getAnimatedValue();
                    invalidate();
                }
            });
            animator.start();
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            paint.setAlpha(20);
            for (int y = 0; y < getHeight(); y += 9) {
                canvas.drawRect(0, y, getWidth(), y + 1, paint);
            }
            paint.setAlpha(phase < 0.16f || (phase > 0.42f && phase < 0.52f) ? 180 : 55);
            float y1 = getHeight() * (0.28f + 0.04f * phase);
            float y2 = getHeight() * (0.67f - 0.03f * phase);
            canvas.drawRect(0, y1, getWidth() * 0.31f, y1 + 3, paint);
            canvas.drawRect(getWidth() * 0.72f, y1 + 28, getWidth(), y1 + 33, paint);
            canvas.drawRect(getWidth() * 0.12f, y2, getWidth() * 0.56f, y2 + 2, paint);
        }
    }
}
