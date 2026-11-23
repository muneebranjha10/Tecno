#!/usr/bin/env python3
"""Improve Tecno Spark 40 demonstration while preserving actual battery telemetry."""
from pathlib import Path
root=Path('TecnoSpark40_LSPosed_Port/app/src/main/java/dev/spark40/charge')
p=root/'ChargeView.java'
s=p.read_text()
def rep(old,new):
 global s
 assert old in s, f'Missing: {old[:90]!r}'
 s=s.replace(old,new,1)
rep('    private int mode;','    private int mode;\n    private boolean previewFastCharge;')
rep('        percent.setTextSize(43);','        percent.setTextSize(42);')
rep('        chargeLabel.setTextSize(13);','        chargeLabel.setTextSize(11);')
rep('        chargeLabel.setText("⚡ CHARGING");','        chargeLabel.setText("CHARGING");')
rep('        captions.setTag("charge-caption");','        captions.setTag("charge-caption");\n        captions.setTranslationY(-dp(16));')
rep('        int initialSide = Math.round(getResources().getDisplayMetrics().widthPixels * 0.78f);','        int initialSide = Math.round(getResources().getDisplayMetrics().widthPixels * 0.92f);')
rep('        int side = Math.round(Math.min(w * 0.78f, h * 0.45f));','        int side = Math.round(Math.min(w * 0.92f, h * 0.47f));')
rep('        if (plugged == BatteryManager.BATTERY_PLUGGED_WIRELESS) {', '''        if (previewFastCharge) {
            mode = 2;
            chargeLabel.setText("⬡ FAST CHARGE");
        } else if (plugged == BatteryManager.BATTERY_PLUGGED_WIRELESS) {''')
rep('            chargeLabel.setText("⚡ WIRELESS CHARGING");','            chargeLabel.setText("⬡ WIRELESS CHARGING");')
rep('            chargeLabel.setText("⚡ FAST CHARGE");','            chargeLabel.setText("⬡ FAST CHARGE");')
rep('            chargeLabel.setText("⚡ CHARGING");','            chargeLabel.setText("CHARGING");')
rep('    public void start() {','''    /** Demo mode changes only the animation/label; battery percentage remains device-derived. */
    public void previewOriginalFastCharge() {
        previewFastCharge = true;
        mode = 2; // Tecno XML frames 150–199, original colored fast-charge ring
        chargeLabel.setText("⬡ FAST CHARGE");
    }

    public void start() {''')
p.write_text(s)
p=root/'MainActivity.java';s=p.read_text()
old='''            preview.updateBattery(registerReceiver(null, new IntentFilter(Intent.ACTION_BATTERY_CHANGED)));
            preview.start();'''
assert old in s
s=s.replace(old,'''            preview.updateBattery(registerReceiver(null, new IntentFilter(Intent.ACTION_BATTERY_CHANGED)));
            // Demonstrate original HiOS colorful FAST CHARGE sequence in preview only.
            // The battery percentage remains real; runtime charge class is not overridden.
            preview.previewOriginalFastCharge();
            preview.start();''',1)
s=s.replace('button.setText("Play preview");','button.setText("Preview original FAST CHARGE effect");',1)
p.write_text(s)
print('v0.3 preview colors, size, typography and original fast-charge sequence patched')
