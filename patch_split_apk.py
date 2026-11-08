#!/usr/bin/env python
"""Patch split APKs with local server IP - modifies global-metadata.dat inside base APK"""
import zipfile
import tempfile
import shutil
from pathlib import Path

WORK_DIR = Path(__file__).parent
BASE_APK = WORK_DIR / "game.apk"
PATCHED_APK = WORK_DIR / "game_patched_final.apk"

METADATA_PATH = "assets/bin/Data/Managed/Metadata/global-metadata.dat"

# URL replacements
REPLACEMENTS = {
    b'https://notice.bigshot-games.xyz': b'http://10.0.2.2:8080' + b'\x00' * 12,
    b'notice.bigshot-games.xyz': b'10.0.2.2:8080' + b'\x00' * 5,
}

print("=" * 60)
print("Patching Split APK - Metadata URL replacement")
print("=" * 60)

# Create temp dir
with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)

    # Extract base APK
    print(f"\n1. Extracting {BASE_APK.name}...")
    with zipfile.ZipFile(BASE_APK, 'r') as zin:
        zin.extractall(tmpdir)

    # Patch metadata
    metadata_file = tmpdir / METADATA_PATH.replace('/', '\\')
    if not metadata_file.exists():
        print(f"ERROR: {METADATA_PATH} not found in APK")
        exit(1)

    print(f"\n2. Patching {METADATA_PATH}...")
    data = metadata_file.read_bytes()
    patched = data
    for old_url, new_url in REPLACEMENTS.items():
        if old_url in patched:
            patched = patched.replace(old_url, new_url)
            print(f"   [OK] {old_url.decode(errors='ignore')[:35]} -> {new_url.decode(errors='ignore')[:20]}")

    metadata_file.write_bytes(patched)

    # Rebuild APK
    print(f"\n3. Rebuilding APK...")
    if PATCHED_APK.exists():
        PATCHED_APK.unlink()

    with zipfile.ZipFile(PATCHED_APK, 'w', zipfile.ZIP_DEFLATED) as zout:
        for file_path in tmpdir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(tmpdir)
                zout.write(file_path, arcname)

size_mb = PATCHED_APK.stat().st_size / 1024 / 1024
print(f"\n[OK] Patched base APK: {PATCHED_APK.name} ({size_mb:.1f} MB)")
print("\nNext: Sign both APKs and install as split")
print("=" * 60)
