param(
    [string]$Serial = "emulator-5554",
    [string]$OutputDir = "$env:USERPROFILE\Desktop\SlayerOriginalClient",
    [switch]$SkipAdb
)

$ErrorActionPreference = "Stop"
New-Item -Path $OutputDir -ItemType Directory -Force | Out-Null

# This script inspects ONLY the original Unity game installation and
# publishes no APK, credentials, raw logcat, or protected XAPK assets.
$report = [ordered]@{
    GamePackage = "com.gear2.growslayer"
    Purpose = "Original Unity client authentication tracing"
    ClientModified = $false
    OriginalApkBuilt = $false
    CapturedAtUtc = [DateTime]::UtcNow.ToString("o")
    Device = $null
    EmulatorAbi = $null
    AppInstalled = $null
    Events = @()
}

if (-not $SkipAdb) {
    $adb = Join-Path $env:LOCALAPPDATA "Android\Sdk\platform-tools\adb.exe"
    if (-not (Test-Path -LiteralPath $adb)) {
        throw "ADB not found: $adb"
    }
    $devices = @(& $adb devices)
    if (-not ($devices | Where-Object { $_ -match "^`$Serial\s+device\s*`$" })) {
        throw "ADB device not connected: $Serial. Run: adb devices"
    }
    $report.Device = $Serial
    $report.EmulatorAbi = (& $adb -s $Serial shell getprop ro.product.cpu.abilist | Out-String).Trim()
    $paths = @(& $adb -s $Serial shell pm path com.gear2.growslayer)
    $report.AppInstalled = [bool]($paths | Where-Object { $_ -match "^package:" })

    # Only permit minimal Unity event names, never token/JWT, email, IDs or raw log lines.
    $patterns = @(
      "Unity\s+: Button_TapToStart\s*$",
      "Unity\s+: lookup [a-z0-9.-]+\s*$",
      "Unity\s+: server address https://[a-z0-9.-]+\s*$",
      "Unity\s+: IFix Patch result : (?:True|False)\s*$",
      "Unity\s+: OnConnected\s*$",
      "Unity\s+: BigIntegerCurrency type \[None\] not found\.\s*$",
      "Unity\s+: SignManager:LoginResult_Func\(LoginResponse\)\s*$",
      "Unity\s+: UserInfoLoad:Load\(UserInfo, Action`1\)\s*$",
      "Unity\s+: Network\.<ValidateAuthAsyncV3>d__35:MoveNext\(\)\s*$",
      "Unity\s+: SceneBase::DestroyScene => SceneTitle_[0-9,.]+\s*$"
    )
    $raw = & $adb -s $Serial logcat -d -v time -s Unity:V "*:S"
    foreach ($line in $raw) {
        foreach ($regex in $patterns) {
            if ($line -match $regex) {
                $time = if ($line -match "^(\d\d-\d\d \d\d:\d\d:\d\d\.\d\d\d)") { $Matches[1] } else { "unknown" }
                $event = ($line -split "Unity\s+:", 2)[-1].Trim()
                $report.Events += [ordered]@{ Time=$time; Event=$event }
                break
            }
        }
    }
}
$xapk = Join-Path $env:USERPROFILE "Downloads\Slayer+Legend+_+Idle+RPG_700.0.4_APKPure.xapk"
if (Test-Path -LiteralPath $xapk) {
    $report.OriginalXapkSha256 = (Get-FileHash -LiteralPath $xapk -Algorithm SHA256).Hash.ToLowerInvariant()
    $report.MatchesStaticResearch = ($report.OriginalXapkSha256 -eq "b8c19d5fdf4da70c8c45cddf3f7e6b8a850863fd55b09b087c6d06d7001d6098")
} else {
    $report.OriginalXapkPresent = $false
}
$target = Join-Path $OutputDir "auth_trace_sanitized.json"
$report | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $target -Encoding UTF8
Write-Host "Original client report: $target"
Write-Host "This tool does not patch the original Unity APK and does not expose secrets."
