#!/usr/bin/env python3
"""
Patch Dungeon Corp APK: replace dead backend URLs with local server
"""
import zipfile
import shutil
import os
from pathlib import Path

WORK_DIR = Path(__file__).parent
APK_ORIG = WORK_DIR / "game.apk"
APK_PATCHED = WORK_DIR / "game_patched.apk"
TEMP_DIR = WORK_DIR / "apk_temp"

# URL replacements: old -> new (new must be <= old length for safe null-pad)
REPLACEMENTS = {
    b'legendaryitem.bigshot-games.xyz:1220': b'10.0.2.2:8080',  # 36 -> 13 bytes
    b'chatting.legendaryitem.bigshot-games.xyz:1220': b'10.0.2.2:8080/chat',  # 45 -> 19 bytes
    b'notice.bigshot-games.xyz': b'10.0.2.2:8080',  # 24 -> 13 bytes
    b'https://notice.bigshot-games.xyz': b'http://10.0.2.2:8080',  # 32 -> 20 bytes
}

def patch_file(data: bytes) -> bytes:
    """Replace all backend URLs, null-pad to original length"""
    patched = data
    for old_url, new_url in REPLACEMENTS.items():
        if old_url in patched:
            # Replace + pad with nulls to keep file structure intact
            padding = b'\x00' * (len(old_url) - len(new_url))
            patched = patched.replace(old_url, new_url + padding)
            print(f"  Replaced {old_url.decode(errors='ignore')} -> {new_url.decode()}")
    return patched

def main():
    print("=" * 60)
    print("Dungeon Corp APK Patcher")
    print("Replacing dead backend with local mock server")
    print("=" * 60)

    if not APK_ORIG.exists():
        print(f"ERROR: {APK_ORIG} not found")
        return

    # Clean temp
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir()

    print(f"\n1. Extracting APK...")
    with zipfile.ZipFile(APK_ORIG, 'r') as zin:
        zin.extractall(TEMP_DIR)

    # Patch global-metadata (main string table)
    metadata_path = TEMP_DIR / "assets/bin/Data/Managed/Metadata/global-metadata.dat"
    if metadata_path.exists():
        print(f"\n2. Patching {metadata_path.name}...")
        data = metadata_path.read_bytes()
        patched = patch_file(data)
        metadata_path.write_bytes(patched)

    # Also patch data.unity3d if it contains URLs
    unity_data = TEMP_DIR / "assets/bin/Data/data.unity3d"
    if unity_data.exists():
        print(f"\n3. Patching {unity_data.name}...")
        data = unity_data.read_bytes()
        if b'bigshot-games' in data:
            patched = patch_file(data)
            unity_data.write_bytes(patched)
        else:
            print("  No URLs found, skipping")

    # Rebuild APK
    print(f"\n4. Rebuilding APK...")
    if APK_PATCHED.exists():
        APK_PATCHED.unlink()

    with zipfile.ZipFile(APK_PATCHED, 'w', zipfile.ZIP_DEFLATED) as zout:
        for root, dirs, files in os.walk(TEMP_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(TEMP_DIR)
                zout.write(file_path, arcname)

    print(f"\n5. Cleanup...")
    shutil.rmtree(TEMP_DIR)

    size_mb = APK_PATCHED.stat().st_size / 1024 / 1024
    print(f"\n✓ Patched APK created: {APK_PATCHED.name} ({size_mb:.1f} MB)")
    print("\nNext steps:")
    print("1. Sign APK: apksigner sign --ks debug.keystore game_patched.apk")
    print("2. Install: adb install -r game_patched.apk")
    print("3. Start mock server on port 8080")
    print("=" * 60)

if __name__ == '__main__':
    main()
