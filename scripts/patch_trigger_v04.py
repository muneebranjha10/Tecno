#!/usr/bin/env python3
"""v0.4: Make real charging triggers robust on Samsung lock screen.
This patch modifies the *bundled original sources* after ZIP extraction.
"""
from pathlib import Path
p = Path("TecnoSpark40_LSPosed_Port/app/src/main/java/dev/spark40/charge/ChargeController.java")
p.write_text(r'''package dev.spark40.charge;

import android.app.Application;
import android.app.KeyguardManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;
import java.lang.ref.WeakReference;

/**
 * Real charger events inside Samsung SystemUI. No window injection or shell calls.
 * If the screen is off or Keyguard is not yet ready, retry on screen-on / host attach.
 * Log tag: Spark40Charge. Leave user unlock, fingerprint and emergency actions untouched.
 */
public final class ChargeController {
    private static final String TAG = "Spark40Charge";
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static final long DISPLAY_MS = 16000L;
    private static final long PENDING_MS = 30000L;

    private static Application app;
    private static Intent batteryIntent;
    private static WeakReference<ViewGroup> host = new WeakReference<>(null);
    private static ChargeView current;
    private static long lastConnectTime;
    private static int lastPlugged = -1;
    private static int generation;

    private ChargeController() {}

    public static void install(Application application) {
        MAIN.post(() -> {
            if (app != null) return;
            app = application;
            IntentFilter filter = new IntentFilter();
            filter.addAction(Intent.ACTION_POWER_CONNECTED);
            filter.addAction(Intent.ACTION_POWER_DISCONNECTED);
            filter.addAction(Intent.ACTION_BATTERY_CHANGED);
            filter.addAction(Intent.ACTION_SCREEN_ON);
            filter.addAction(Intent.ACTION_SCREEN_OFF);
            filter.addAction(Intent.ACTION_USER_PRESENT);
            try {
                Intent initial;
                // Samsung power broadcasts can originate in privileged processes.
                // The old NOT_EXPORTED receiver could miss those broadcasts.
                if (Build.VERSION.SDK_INT >= 33) {
                    initial = app.registerReceiver(receiver, filter, Context.RECEIVER_EXPORTED);
                } else {
                    initial = app.registerReceiver(receiver, filter);
                }
                if (initial != null && Intent.ACTION_BATTERY_CHANGED.equals(initial.getAction())) {
                    batteryIntent = initial;
                    lastPlugged = initial.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0);
                }
                Log.i(TAG, "Receiver registered; initial plugged=" + lastPlugged);
            } catch (Throwable t) {
                Log.e(TAG, "Receiver registration failed", t);
            }
        });
    }

    public static void attach(ViewGroup view) {
        MAIN.post(() -> {
            host = new WeakReference<>(view);
            Log.i(TAG, "NotificationShadeWindowView attached=" + view.isAttachedToWindow());
            if (pending()) scheduleShow("shade attached");
        });
    }

    private static boolean pending() {
        long age = SystemClock.elapsedRealtime() - lastConnectTime;
        return lastConnectTime > 0 && age >= 0 && age <= PENDING_MS;
    }

    private static void arm(String reason) {
        long now = SystemClock.elapsedRealtime();
        if (lastConnectTime != 0 && now - lastConnectTime < 1300) return;
        lastConnectTime = now;
        Log.i(TAG, "Charging event received: " + reason);
        scheduleShow(reason);
        // On Samsung, Keyguard may attach shortly *after* a charging event.
        MAIN.postDelayed(() -> { if (pending()) scheduleShow("retry 450ms"); }, 450);
        MAIN.postDelayed(() -> { if (pending()) scheduleShow("retry 1250ms"); }, 1250);
    }

    private static void scheduleShow(String reason) {
        MAIN.post(() -> attemptShow(reason));
    }

    private static void attemptShow(String reason) {
        if (!pending() || current != null) return;
        if (app == null) {
            Log.w(TAG, "Waiting for SystemUI application: " + reason);
            return;
        }
        PowerManager pm = (PowerManager) app.getSystemService(Context.POWER_SERVICE);
        if (pm != null && !pm.isInteractive()) {
            Log.i(TAG, "Deferred; screen off: " + reason);
            return;
        }
        KeyguardManager kg = (KeyguardManager) app.getSystemService(Context.KEYGUARD_SERVICE);
        if (kg == null || !kg.isKeyguardLocked()) {
            Log.i(TAG, "Deferred; device unlocked or Keyguard not yet ready: " + reason);
            return;
        }
        ViewGroup root = host.get();
        if (root == null || !root.isAttachedToWindow()) {
            Log.w(TAG, "Deferred; Samsung lock-screen host unavailable: " + reason);
            return;
        }
        try {
            // Always fetch newest battery data for real percentage/mode.
            Intent latest = app.registerReceiver(null,
                    new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
            if (latest != null) batteryIntent = latest;

            Context moduleContext = app.createPackageContext("dev.spark40.charge", 0);
            ChargeView display = new ChargeView(moduleContext);
            display.setClickable(false);
            display.setFocusable(false);
            display.setImportantForAccessibility(
                    View.IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS);
            root.addView(display, new ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT));
            display.bringToFront();
            current = display;
            display.updateBattery(batteryIntent);
            display.setAlpha(0f);
            display.animate().alpha(1f).setDuration(220).start();
            display.start();
            Log.i(TAG, "SUCCESS: animation attached to Keyguard; reason=" + reason);
            final int token = ++generation;
            MAIN.postDelayed(() -> {
                if (generation == token) hide();
            }, DISPLAY_MS);
        } catch (Throwable t) {
            Log.e(TAG, "FAILED to attach charging animation", t);
            hideNow();
        }
    }

    private static final BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (action == null) return;
            switch (action) {
                case Intent.ACTION_BATTERY_CHANGED: {
                    batteryIntent = intent;
                    if (current != null) current.updateBattery(intent);
                    int plugged = intent.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0);
                    if (lastPlugged == 0 && plugged != 0) arm("battery charging transition");
                    else if (lastPlugged > 0 && plugged == 0) {
                        lastConnectTime = 0;
                        hide();
                    }
                    lastPlugged = plugged;
                    break;
                }
                case Intent.ACTION_POWER_CONNECTED:
                    arm("ACTION_POWER_CONNECTED");
                    break;
                case Intent.ACTION_POWER_DISCONNECTED:
                    lastConnectTime = 0;
                    lastPlugged = 0;
                    hide();
                    break;
                case Intent.ACTION_SCREEN_OFF:
                    // Do not lose the plug-in event: retry if charging wakes the screen.
                    hide();
                    break;
                case Intent.ACTION_SCREEN_ON:
                    if (pending()) {
                        scheduleShow("screen on");
                        MAIN.postDelayed(() -> {
                            if (pending()) scheduleShow("Keyguard screen-on retry");
                        }, 750);
                        MAIN.postDelayed(() -> {
                            if (pending()) scheduleShow("Keyguard screen-on 2s retry");
                        }, 2000);
                    }
                    break;
                case Intent.ACTION_USER_PRESENT:
                    // Stop displaying once the user unlocks.
                    lastConnectTime = 0;
                    hide();
                    break;
                default:
                    break;
            }
        }
    };

    private static void hide() {
        MAIN.post(() -> {
            if (current == null) return;
            final ChargeView view = current;
            current = null;
            ++generation;
            view.animate().alpha(0f).setDuration(180)
                    .withEndAction(() -> remove(view)).start();
        });
    }

    private static void hideNow() {
        if (current != null) {
            current.animate().cancel();
            remove(current);
            current = null;
        }
        ++generation;
    }

    private static void remove(ChargeView view) {
        view.stop();
        if (view.getParent() instanceof ViewGroup) {
            ((ViewGroup) view.getParent()).removeView(view);
        }
    }
}
''')

h = Path("TecnoSpark40_LSPosed_Port/app/src/main/java/dev/spark40/charge/HookEntry.java")
s = h.read_text()
needle = '''        try {
            XposedHelpers.findAndHookMethod("com.android.systemui.SystemUIApplication",'''
assert needle in s
s = s.replace(needle, '''        Log.i(TAG, "LSPosed entry loaded in " + lpparam.processName);

        try {
            XposedHelpers.findAndHookMethod("com.android.systemui.SystemUIApplication",''',1)
h.write_text(s)
print("v0.4: robust charger + screen-on + battery transition triggers, diagnostic logs")
