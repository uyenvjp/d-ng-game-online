@echo off
REM Start Android Emulator
echo Starting Android Emulator...

set ANDROID_SDK_ROOT=C:\Users\okokok\AppData\Local\Android\Sdk
set EMULATOR=%ANDROID_SDK_ROOT%\emulator\emulator.exe

if not exist "%EMULATOR%" (
    echo [ERROR] Android SDK not found at: %ANDROID_SDK_ROOT%
    echo.
    echo Please install Android Studio or Android SDK first
    echo Download from: https://developer.android.com/studio
    pause
    exit /b 1
)

REM List available AVDs
echo.
echo Available emulators:
"%EMULATOR%" -list-avds

echo.
echo Starting emulator (this may take a few minutes)...
start "" "%EMULATOR%" -avd DungeonRoot -no-snapshot-load

echo.
echo Waiting for device to boot...
timeout /t 10

C:\Users\okokok\Desktop\dungeon-re\platform-tools\adb.exe wait-for-device
echo.
echo [OK] Emulator is ready!
echo.
echo Now run: python install_and_run.py
pause
