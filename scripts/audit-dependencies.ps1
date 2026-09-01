[CmdletBinding()]
param(
    [string]$ComposeFile = "deploy/docker/docker-compose.yml",
    [string]$EnvironmentFile = "deploy/docker/.env"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $EnvironmentFile)) {
    throw "Missing $EnvironmentFile. Copy deploy/docker/.env.example and provide real non-placeholder secrets."
}
New-Item -ItemType Directory -Force -Path reports | Out-Null
docker compose --env-file $EnvironmentFile -f $ComposeFile --profile audit build audit
docker compose --env-file $EnvironmentFile -f $ComposeFile --profile audit run --rm audit
Get-ChildItem reports/pip-audit.json, reports/safety.json, reports/python-dependencies.txt, reports/audit-summary.txt |
    Select-Object Name, Length, LastWriteTime
