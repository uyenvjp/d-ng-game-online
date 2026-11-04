@echo off
setlocal
set "PROJECT_DIR=%~dp0"
set "STUDIO=C:\Program Files\Android\Android Studio\bin\studio64.exe"
if not exist "%PROJECT_DIR%settings.gradle" (
  echo Cannot find settings.gradle inside the same folder as this launcher.
  pause
  exit /b 1
)
if not exist "%STUDIO%" (
  echo Cannot find Android Studio at %STUDIO%
  echo Open Android Studio manually and choose:
  echo %PROJECT_DIR%
  pause
  exit /b 1
)
echo Opening Android project:
echo %PROJECT_DIR%
start "" "%STUDIO%" "%PROJECT_DIR%"
endlocal
