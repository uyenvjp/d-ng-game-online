# Slayer Private Login — standalone Android debug APK

**Scope:** a standalone OFFLINE login/signup APK. **Not** the original Slayer Legend client, **not** a LIAPP replacement, and **not** a connected online backend.

- Java Android Activity; no third-party UI dependencies or game assets
- Register offline, sign in offline, sign out
- Account records kept on this Android device in SharedPreferences
- Password stored as random-salted PBKDF2-HMAC-SHA256 hash (180,000 rounds)
- Android min SDK 26, compile SDK 35
- GitHub Actions builds a debug-signed APK artifact

## Downloading the APK

On GitHub, open **Actions → Build Slayer Login Debug APK → latest successful run → Artifacts → slayer-login-debug-apk**. Download the ZIP and extract **app-debug.apk**.

## Build manually

Requires JDK 17, Android SDK 35, Gradle 8.7:

    cd slayer-login-android
    gradle :app:assembleDebug

APK output:

    app/build/outputs/apk/debug/app-debug.apk

## Boundaries

This prototype only validates the login UI and local password flow. It does not issue server sessions, perform any Google/Apple sign-in, patch Unity/IL2CPP, bypass LIAPP, or modify game assets. Do not use the local credential system as a production multiplayer identity provider; a separate authenticated backend is required.
