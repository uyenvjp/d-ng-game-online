$lines = @"
127.0.0.1 notice.bigshot-games.xyz
127.0.0.1 api.bigshot-games.xyz
127.0.0.1 bigshot-games.xyz
"@
Add-Content -Path "C:\Windows\System32\drivers\etc\hosts" -Value $lines -Encoding ASCII
Write-Host "hosts updated"
