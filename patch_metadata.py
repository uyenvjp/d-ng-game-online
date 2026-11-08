#!/usr/bin/env python
"""Patch server URLs in APK metadata before rebuild"""
import sys

metadata_path = 'apktool_out/assets/bin/Data/Managed/Metadata/global-metadata.dat'

# Read and patch metadata
data = open(metadata_path, 'rb').read()
replacements = {
    b'https://notice.bigshot-games.xyz': b'http://10.0.2.2:8080' + b'\x00' * 12,
    b'notice.bigshot-games.xyz': b'10.0.2.2:8080' + b'\x00' * 5,
}

patched = data
for old, new in replacements.items():
    if old in patched:
        patched = patched.replace(old, new)
        print(f'Patched: {old.decode(errors="ignore")[:40]} -> {new.decode(errors="ignore")[:20]}')

open(metadata_path, 'wb').write(patched)
print('Metadata patched, rebuild APK now.')
