# Slayer Login APK V2 — Offline + Optional Private Server

**Important:** this is an independent Android authentication prototype. It is NOT the original Slayer Legend Unity client, has no gameplay, and does not patch, bypass or replace LIAPP.

## Android features
- Offline registration/login/logout on the original local screen (V1).
- New ĐĂNG NHẬP SERVER (V2) screen for private backend accounts.
- HTTPS only, using the system's trusted TLS certificate validation.
- Stores the successful bearer token as Android Keystore AES-GCM ciphertext; clear token or revoke it on the backend.
- No proprietary art, Unity assets, or third-party game data.

## Private backend (optional)
Node.js 24 + built-in SQLite. No XAMPP, PHP, or database server install necessary.

    cd slayer-login-android/backend
    node --test
    node server.mjs

By default, binds to 127.0.0.1:8787. Do not open this plain HTTP port to the Internet. Deploy behind an HTTPS reverse proxy on a domain controlled by the operator. Enter that HTTPS origin in the Android screen. No backend is deployed automatically.

Routes:
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET /api/v1/auth/me (Bearer token)
- POST /api/v1/auth/logout (Bearer token)
- GET /health

Account secrets are derived with scrypt and independent random salts, session tokens are generated with crypto.randomBytes and only SHA256 hashes are stored in SQLite. Additional production work: trusted reverse proxy, account recovery, TLS infrastructure, monitoring, migrations, and backups.

## Build APK
GitHub Actions compiles the V2 debug-signed APK and publishes it in the repository Releases. Or build manually:

    cd slayer-login-android
    gradle :app:assembleDebug

Requires Android SDK 35, JDK 17, Gradle 8.7.

## Original Slayer Legend integration
Still NOT implemented. Previous static research found SignManager.Button_TapToStart, Integration.LookupLoginResponse.IsNewUser, GrowSlayer.SignUpV2Request and UserInfoLoadEquipment; the original runtime relies on LIAPP, IFix, and services which have not been reproduced or safely replaced. Do not treat a successful login in this demo as login to the original game.
