$path = "C:\Windows\System32\drivers\etc\hosts"
$content = Get-Content $path -Raw
$fixed = $content -replace "helper server127\.0\.0\.1 notice", "helper server`r`n127.0.0.1 notice"
Set-Content -Path $path -Value $fixed -Encoding ASCII -NoNewline
Write-Host "fixed"
