param(
  [string]$Serial = 'emulator-5554',
  [string]$OutputDir = "$HOME\Desktop\SlayerOriginalClient",
  [switch]$SkipAdb
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$report = [ordered]@{
  GamePackage = 'com.gear2.growslayer'
  Source = 'Original Slayer Legend client'
  ClientModified = $false
  OriginalApkBuilt = $false
  Emulator = $Serial
  Events = @()
}
if (-not $SkipAdb) {
  $adb = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
  if (-not (Test-Path -LiteralPath $adb)) { throw "Missing ADB: $adb" }
  $connected = @(& $adb devices)
  $expected = '^{0}\s+device\s*$' -f [Regex]::Escape($Serial)
  if (-not ($connected | Where-Object { $_ -match $expected })) {
    throw "Emulator $Serial not connected"
  }
  $report.CpuAbi = (& $adb -s $Serial shell getprop ro.product.cpu.abilist | Out-String).Trim()
  $installed = @(& $adb -s $Serial shell pm path com.gear2.growslayer)
  $report.GameInstalled = [bool]($installed | Where-Object { $_ -match '^package:' })
  $allowed = @(
    '^Button_TapToStart$',
    '^lookup [a-z0-9.-]+$',
    '^server address https://[a-z0-9.-]+$',
    '^IFix Patch result : (?:True|False)$',
    '^OnConnected$',
    '^BigIntegerCurrency type \[None\] not found\.$',
    '^SignManager:LoginResult_Func\(LoginResponse\)$',
    '^UserInfoLoad:Load\(',
    '^Network\.<ValidateAuthAsyncV3>d__35:MoveNext\(\)$'
  )
  foreach ($line in (& $adb -s $Serial logcat -d -v time -s 'Unity:V' '*:S')) {
    if ($line -notmatch 'Unity\s+: (.*)$') { continue }
    $event = $Matches[1].Trim()
    foreach ($pattern in $allowed) {
      if ($event -match $pattern) {
        $ts = if ($line -match '^(\d\d-\d\d \d\d:\d\d:\d\d\.\d\d\d)') { $Matches[1] } else { 'unknown' }
        $report.Events += [ordered]@{Time=$ts;Event=$event}
        break
      }
    }
  }
}
$destination = Join-Path $OutputDir 'auth_trace_sanitized.json'
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $destination -Encoding UTF8
Write-Host "Report: $destination"
Write-Host 'Only selected Unity event names saved. NO tokens or original game files.'
