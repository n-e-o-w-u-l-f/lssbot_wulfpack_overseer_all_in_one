param(
  [switch]$InstallConfig,
  [switch]$Validate
)
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot\..
if ($InstallConfig) { py -3 .\src\lss_sidecar_v4_4.py --install-config; exit $LASTEXITCODE }
if ($Validate) { py -3 .\src\lss_sidecar_v4_4.py --validate --config .\config\sidecar_config.json; exit $LASTEXITCODE }
py -3 .\src\lss_sidecar_v4_4.py --config .\config\sidecar_config.json
