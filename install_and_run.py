#!/usr/bin/env python3
"""Install and run the patched game APK"""
import subprocess
import time
import sys
from pathlib import Path

WORK_DIR = Path(__file__).parent
ADB = WORK_DIR / "platform-tools" / "adb.exe"
BASE_APK = WORK_DIR / "game_base_signed.apk"
SPLIT_APK = WORK_DIR / "split_arm64_signed.apk"

def run_cmd(cmd, check=True):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result

print("=" * 60)
print("Installing and Running Patched Game")
print("=" * 60)

# Check device connection
print("\n1. Checking device connection...")
result = run_cmd([ADB, "devices"], check=False)
lines = result.stdout.strip().split('\n')
devices = [l for l in lines[1:] if l.strip() and 'device' in l]

if not devices:
    print("\n[ERROR] No device/emulator connected!")
    print("\nOptions:")
    print("1. Connect a physical device via USB")
    print("2. Start an Android emulator")
    print("3. Use Android Studio AVD Manager to create/start an emulator")
    sys.exit(1)

print(f"[OK] Found device: {devices[0]}")

# Uninstall old version
print("\n2. Uninstalling old version...")
pkg_name = "com.bigshotgames.dungeon"
run_cmd([ADB, "uninstall", pkg_name], check=False)

# Install split APKs
print("\n3. Installing split APKs...")
if not BASE_APK.exists():
    print(f"[ERROR] Base APK not found: {BASE_APK}")
    sys.exit(1)
if not SPLIT_APK.exists():
    print(f"[ERROR] Split APK not found: {SPLIT_APK}")
    sys.exit(1)

run_cmd([ADB, "install-multiple", str(BASE_APK), str(SPLIT_APK)])

# Launch the app
print("\n4. Launching game...")
run_cmd([ADB, "shell", "am", "start", "-n", f"{pkg_name}/.MainActivity"], check=False)

print("\n" + "=" * 60)
print("[OK] Game installed and launched!")
print("=" * 60)
print("\nMonitor logs with:")
print(f"  {ADB} logcat | grep -i unity")
