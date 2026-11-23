#!/usr/bin/env python3
"""Fix square Tecno charge ring layout in the bundled alpha source project."""
from pathlib import Path

root = Path("TecnoSpark40_LSPosed_Port/app/src/main/java/dev/spark40/charge")
p = root / "ChargeView.java"
s = p.read_text()

def change(before, after):
    global s
    if before not in s:
        raise RuntimeError("Unexpected source: could not locate " + before[:80])
    s = s.replace(before, after, 1)

change(
    "    private final ImageView ring;\n    private final TextView percent;",
    "    private final ImageView ring;\n    private final FrameLayout orbStage;\n    private final LinearLayout captions;\n    private final TextView percent;"
)
change(
    """        ring = new ImageView(context);
        ring.setScaleType(ImageView.ScaleType.FIT_XY);
        ring.setClickable(false);
        ring.setFocusable(false);
        addView(ring);

        LinearLayout captions = new LinearLayout(context);""",
    """        // Preserve the source video aspect ratio (Tecno XML gravity=2).
        // A square stage prevents the old full-screen oval distortion.
        int initialSide = Math.round(getResources().getDisplayMetrics().widthPixels * 0.78f);
        orbStage = new FrameLayout(context);
        LayoutParams stageParams = new LayoutParams(initialSide, initialSide,
                Gravity.TOP | Gravity.CENTER_HORIZONTAL);
        stageParams.topMargin = Math.round(
                getResources().getDisplayMetrics().heightPixels * 0.36f - initialSide / 2f);
        addView(orbStage, stageParams);

        ring = new ImageView(context);
        ring.setScaleType(ImageView.ScaleType.FIT_CENTER);
        ring.setClickable(false);
        ring.setFocusable(false);
        orbStage.addView(ring, new FrameLayout.LayoutParams(
                LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT, Gravity.CENTER));

        captions = new LinearLayout(context);"""
)
change(
    """        captions.setTag("charge-caption");
        addView(captions);""",
    """        captions.setTag("charge-caption");
        orbStage.addView(captions, new FrameLayout.LayoutParams(
                LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT, Gravity.CENTER));"""
)
a = s.index("    @Override protected void onSizeChanged(")
b = s.index("    public void updateBattery(", a)
s = s[:a] + """    @Override protected void onSizeChanged(int w, int h, int oldw, int oldh) {
        super.onSizeChanged(w, h, oldw, oldh);
        if (w <= 0 || h <= 0) return;
        // Original ring must remain a perfect circle, centered at 36% screen height.
        int side = Math.round(Math.min(w * 0.78f, h * 0.45f));
        int top = Math.round(h * 0.36f) - side / 2;
        LayoutParams params = (LayoutParams) orbStage.getLayoutParams();
        if (params.width != side || params.height != side || params.topMargin != top) {
            params.width = side;
            params.height = side;
            params.topMargin = top;
            orbStage.setLayoutParams(params);
        }
    }

""" + s[b:]
change(
    """        started = true;
        showAnimation("charge/entry.webp", false);""",
    """        started = true;
        // Match original Tecno XML enterAnimDelayTime/enterAnimDuration.
        captions.setAlpha(0f);
        captions.animate().alpha(1f).setStartDelay(250).setDuration(250).start();
        showAnimation("charge/entry.webp", false);"""
)
change("        stopped = true;\n        if (animation != null)", "        stopped = true;\n        captions.animate().cancel();\n        if (animation != null)")
p.write_text(s)
controller = root / "ChargeController.java"
x = controller.read_text()
assert "DISPLAY_MS = 8500L" in x
controller.write_text(x.replace("DISPLAY_MS = 8500L", "DISPLAY_MS = 16000L", 1))
preview = root / "MainActivity.java"
x = preview.read_text()
assert "}, 8500);" in x
preview.write_text(x.replace("}, 8500);", "}, 16000);", 1))
print("Applied square-ring fix, center captions, and Tecno timing.")
