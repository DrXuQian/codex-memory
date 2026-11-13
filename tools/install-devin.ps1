# Install this pack's skills as global Devin skills so they work from any directory.
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Dest = Join-Path $env:APPDATA "devin\skills"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Get-ChildItem (Join-Path $Root ".devin\skills") -Directory | ForEach-Object {
    $target = Join-Path $Dest $_.Name
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    Copy-Item -Recurse $_.FullName $target
    Write-Host "installed $($_.Name) -> $target"
}
$skill = Join-Path $Dest "codex-history\SKILL.md"
(Get-Content -Raw -Encoding UTF8 $skill).Replace("{{PACK_ROOT}}", ($Root -replace "\\", "/")) |
    Set-Content -NoNewline -Encoding UTF8 $skill
Write-Host "codex-history PACK_ROOT = $Root"
