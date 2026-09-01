[CmdletBinding()]
param(
    [string]$ComposeFile = "deploy/docker/docker-compose.yml",
    [string]$EnvironmentFile = "deploy/docker/.env"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-Status([string]$Name, [string]$Uri, [int]$ExpectedStatus = 200) {
    $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing
    if ($response.StatusCode -ne $ExpectedStatus) {
        throw "$Name returned HTTP $($response.StatusCode), expected $ExpectedStatus."
    }
    Write-Host "PASS: $Name ($ExpectedStatus)"
    return $response
}

if (-not (Test-Path $EnvironmentFile)) {
    throw "Missing $EnvironmentFile. Copy deploy/docker/.env.example and provide real non-placeholder secrets."
}

docker compose --env-file $EnvironmentFile -f $ComposeFile config --quiet
docker compose --env-file $EnvironmentFile -f $ComposeFile build
docker compose --env-file $EnvironmentFile -f $ComposeFile up --detach --wait --wait-timeout 180

$migrationState = docker compose --env-file $EnvironmentFile -f $ComposeFile ps --format json migrations | ConvertFrom-Json
if ($migrationState.ExitCode -ne 0) { throw "Alembic migration service did not complete successfully." }
Write-Host "PASS: Alembic migration completed"

Assert-Status "backend liveness" "http://localhost:8000/health/live" | Out-Null
Assert-Status "backend readiness" "http://localhost:8000/health/ready" | Out-Null
Assert-Status "backend metrics" "http://localhost:8000/metrics" | Out-Null
Assert-Status "frontend health" "http://localhost:8080/health" | Out-Null

$email = "rc-$([guid]::NewGuid().ToString('N').Substring(0, 12))@example.test"
$password = "ReleaseCandidate!123"
$registration = @{ email = $email; username = "rc_$([guid]::NewGuid().ToString('N').Substring(0, 10))"; password = $password; full_name = "Release Candidate" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/auth/register" -ContentType "application/json" -Body $registration | Out-Null
$token = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/auth/login" -ContentType "application/json" -Body (@{ email = $email; password = $password } | ConvertTo-Json)
if (-not $token.access_token) { throw "Authentication did not return an access token." }
$headers = @{ Authorization = "Bearer $($token.access_token)"; "X-Correlation-ID" = "rc-rehearsal-$([guid]::NewGuid())" }
Write-Host "PASS: authentication"

$conversation = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/conversations/" -Headers $headers -ContentType "application/json" -Body (@{ title = "RC validation" } | ConvertTo-Json)
if (-not $conversation.id) { throw "Conversation API did not create a conversation." }
Write-Host "PASS: conversation API"

$tool = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/tools/" -Headers $headers -ContentType "application/json" -Body (@{ name = "rc-tool"; display_name = "RC Tool"; description = "Release validation tool" } | ConvertTo-Json)
if (-not $tool.id) { throw "Tool calling API did not create a tool." }
Write-Host "PASS: tool calling API"

$memory = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/memory/" -Headers $headers -ContentType "application/json" -Body (@{ content = "Release candidate validation memory"; conversation_id = $conversation.id } | ConvertTo-Json)
if (-not $memory.id) { throw "Memory service did not create memory." }
Write-Host "PASS: memory service"

$metrics = (Assert-Status "Prometheus target" "http://localhost:9090/-/ready").Content
Write-Host "PASS: Prometheus readiness"
Assert-Status "Grafana health" "http://localhost:3000/api/health" | Out-Null
Write-Host "PASS: Grafana health"

Write-Host "RC Compose validation completed successfully."
