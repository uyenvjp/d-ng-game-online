#!/usr/bin/env python
"""Patch APK metadata and rebuild properly aligned for Android R+"""
import zipfile
import tempfile
import subprocess
from pathlib import Path

WORK_DIR = Path(__file__).parent
BASE_APK = WORK_DIR / "game.apk"
SPLIT_APK = WORK_DIR / "split_arm64.apk"
PATCHED_BASE = WORK_DIR / "base_patched.apk"
ALIGNED_BASE = WORK_DIR / "base_aligned.apk"
ALIGNED_SPLIT = WORK_DIR / "split_aligned.apk"

SDK = Path("c:/Users/okokok/AppData/Local/Android/SDK")
ZIPALIGN = SDK / "build-tools/34.0.0/zipalign.exe"
APKSIGNER = SDK / "build-tools/34.0.0/apksigner.bat"
ADB = SDK / "platform-tools/adb.exe"

METADATA_PATH = "assets/bin/Data/Managed/Metadata/global-metadata.dat"
REPLACEMENTS = {
    b'https://notice.bigshot-games.xyz': b'http://10.0.2.2:8080' + b'\x00' * 12,
    b'notice.bigshot-games.xyz': b'10.0.2.2:8080' + b'\x00' * 5,
}

print("="*60)
print("Dungeon APK Patcher - Android R+ compatible")
print("="*60)

# Step 1: Patch metadata in base APK
print("\n[1/6] Patching metadata...")
with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    with zipfile.ZipFile(BASE_APK, 'r') as zin:
        zin.extractall(tmpdir)

    metadata_file = tmpdir / METADATA_PATH.replace('/', '\\')
    data = metadata_file.read_bytes()
    patched = data
    for old_url, new_url in REPLACEMENTS.items():
        if old_url in patched:
            patched = patched.replace(old_url, new_url)
            print(f"  Patched: {old_url.decode(errors='ignore')[:35]}")

    metadata_file.write_bytes(patched)

    # Rebuild with STORED compression for resources.arsc
    if PATCHED_BASE.exists():
        PATCHED_BASE.unlink()

    with zipfile.ZipFile(PATCHED_BASE, 'w') as zout:
        for file_path in tmpdir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(tmpdir)
                # Store resources.arsc uncompressed (Android R+ requirement)
                if arcname.name == 'resources.arsc':
                    zout.write(file_path, arcname, compress_type=zipfile.ZIP_STORED)
                else:
                    zout.write(file_path, arcname, compress_type=zipfile.ZIP_DEFLATED)

print(f"  Created: {PATCHED_BASE.name}")

# Step 2: Zipalign base APK
print("\n[2/6] Aligning base APK...")
if ALIGNED_BASE.exists():
    ALIGNED_BASE.unlink()
subprocess.run([str(ZIPALIGN), "-p", "-f", "4", str(PATCHED_BASE), str(ALIGNED_BASE)], check=True)
print(f"  Created: {ALIGNED_BASE.name}")

# Step 3: Zipalign split APK
print("\n[3/6] Aligning split APK...")
if ALIGNED_SPLIT.exists():
    ALIGNED_SPLIT.unlink()
subprocess.run([str(ZIPALIGN), "-p", "-f", "4", str(SPLIT_APK), str(ALIGNED_SPLIT)], check=True)
print(f"  Created: {ALIGNED_SPLIT.name}")

# Step 4: Sign base APK
print("\n[4/6] Signing base APK...")
signed_base = WORK_DIR / "base_signed.apk"
if signed_base.exists():
    signed_base.unlink()
subprocess.run([
    str(APKSIGNER), "sign",
    "--ks", "debug.keystore",
    "--ks-pass", "pass:android",
    "--key-pass", "pass:android",
    "--out", str(signed_base),
    str(ALIGNED_BASE)
], check=True, env={"JAVA_HOME": "c:/Program Files/Android/Android Studio/jbr"})
print(f"  Created: {signed_base.name}")

# Step 5: Sign split APK
print("\n[5/6] Signing split APK...")
signed_split = WORK_DIR / "split_signed.apk"
if signed_split.exists():
    signed_split.unlink()
subprocess.run([
    str(APKSIGNER), "sign",
    "--ks", "debug.keystore",
    "--ks-pass", "pass:android",
    "--key-pass", "pass:android",
    "--out", str(signed_split),
    str(ALIGNED_SPLIT)
], check=True, env={"JAVA_HOME": "c:/Program Files/Android/Android Studio/jbr"})
print(f"  Created: {signed_split.name}")

# Step 6: Install to emulator
print("\n[6/6] Installing to emulator...")
result = subprocess.run([
    str(ADB), "install-multiple",
    str(signed_base), str(signed_split)
], capture_output=True, text=True)

if result.returncode == 0:
    print("  [OK] Installed successfully!")
    print("\n" + "="*60)
    print("APK installed with server URL: http://10.0.2.2:8080")
    print("Launch game: adb shell am start -n com.bigshotgames.legendaryItem/.UnityPlayerActivity")
    print("="*60)
else:
    print(f"  [ERROR] {result.stderr}")
