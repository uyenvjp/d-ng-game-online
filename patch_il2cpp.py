#!/usr/bin/env python3
"""
Patch libil2cpp.so to bypass PlayGames authentication
Replace authentication functions with MOV W0, #1; RET (return true)
"""
from pathlib import Path

WORK_DIR = Path(__file__).parent
LIB_ORIGINAL = WORK_DIR / "apk-extract/lib/arm64-v8a/libil2cpp.so"
LIB_PATCHED = WORK_DIR / "apk-extract/lib/arm64-v8a/libil2cpp_patched.so"

# ARM64 instructions
# MOV W0, #1: 20 00 80 52
# RET:        C0 03 5F D6
PATCH_BYTES = bytes([0x20, 0x00, 0x80, 0x52, 0xC0, 0x03, 0x5F, 0xD6])

# Addresses from IL2CppDumper script.json
# PlayGamesPlatform::IsAuthenticated() and related methods
PATCH_OFFSETS = [
    0x252c8d0,  # PlayGamesPlatform$$IsAuthenticated
    0x25342ec,  # AndroidClient$$IsAuthenticated
    0x2551cb0,  # DummyClient$$IsAuthenticated
]

print("=" * 60)
print("IL2CPP Authentication Patcher")
print("=" * 60)

if not LIB_ORIGINAL.exists():
    print(f"ERROR: {LIB_ORIGINAL} not found")
    exit(1)

# Read original library
lib_data = bytearray(LIB_ORIGINAL.read_bytes())
print(f"Loaded libil2cpp.so: {len(lib_data)} bytes")

# Apply patches
patched_count = 0
for offset in PATCH_OFFSETS:
    if offset < len(lib_data) - len(PATCH_BYTES):
        lib_data[offset:offset+len(PATCH_BYTES)] = PATCH_BYTES
        patched_count += 1
        print(f"  Patched function at 0x{offset:x}")

if patched_count == 0:
    print("\nNo offsets to patch. Need to extract from script.json first.")
    print("Run: python extract_auth_addresses.py")
else:
    # Write patched library
    LIB_PATCHED.write_bytes(lib_data)
    print(f"\nPatched {patched_count} functions")
    print(f"Output: {LIB_PATCHED.name}")
    print("\nNext: Rebuild APK with patched libil2cpp.so")

print("=" * 60)
