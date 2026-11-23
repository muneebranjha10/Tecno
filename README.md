# Tecno Spark 40 Charging Animation → Samsung (LSPosed)

This repository includes a **GitHub Actions APK builder** for the source archive `TecnoSpark40_LSPosed_Source_Alpha.zip`.

## From your Android phone

1. Download the source ZIP from the ChatGPT conversation to your phone. **Do not extract it.**
2. Open the repository in a browser using Desktop site if necessary.
3. Click **Add file → Upload files** and upload `TecnoSpark40_LSPosed_Source_Alpha.zip` to the **root of the `main` branch**. Commit it.
4. Open **Actions → Build Tecno Spark 40 LSPosed APK**. The upload triggers a run automatically; alternatively choose **Run workflow**.
5. After a successful run, open the run → **Artifacts** → `Tecno-Spark40-Charge-LSPosed-APK`.
6. Download the artifact ZIP, unzip it, and install `app-debug.apk` on the Samsung S23.
7. In LSPosed Manager, enable the module for **System UI (`com.android.systemui`)** only. Reboot and test.

**Experimental:** This APK has not yet been built or verified on your Samsung. If SystemUI misbehaves, disable the module in LSPosed and reboot. No Samsung system APK replacement is required.

The archive is about 14 MB because it includes original Tecno animation assets. GitHub's browser upload accepts this size. Keep the original archive filename exactly as given or the build workflow will not detect it.
