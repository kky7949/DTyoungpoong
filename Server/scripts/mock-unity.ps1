param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$PollSeconds = 1,
    [switch]$Once
)

$ErrorActionPreference = "Stop"
$base = $BaseUrl.TrimEnd("/")

Write-Host "Mock Unity connected to $base"

do {
    try {
        $response = Invoke-WebRequest `
            -UseBasicParsing `
            -Uri "$base/api/v1/factory/commands/next" `
            -Method Get

        if ($response.StatusCode -eq 200) {
            $command = $response.Content | ConvertFrom-Json
            Write-Host "Command received: $($command.command_id)"

            $running = @{
                command_id = $command.command_id
                state = "running"
                progress_pct = 35
                message = "Mock Unity process running"
            } | ConvertTo-Json

            Invoke-RestMethod `
                -Uri "$base/api/v1/factory/status" `
                -Method Post `
                -ContentType "application/json; charset=utf-8" `
                -Body $running | Out-Null

            Start-Sleep -Seconds 1

            $completed = @{
                command_id = $command.command_id
                state = "completed"
                progress_pct = 100
                message = "Mock Unity process completed"
            } | ConvertTo-Json

            Invoke-RestMethod `
                -Uri "$base/api/v1/factory/status" `
                -Method Post `
                -ContentType "application/json; charset=utf-8" `
                -Body $completed | Out-Null

            Write-Host "Command completed: $($command.command_id)"
        }
    }
    catch {
        $statusCode = if ($null -ne $_.Exception.Response) {
            [int]$_.Exception.Response.StatusCode
        }
        else {
            $null
        }
        if ($statusCode -ne 204) {
            Write-Warning "FastAPI request failed: $($_.Exception.Message)"
        }
    }

    if (-not $Once) {
        Start-Sleep -Seconds $PollSeconds
    }
} while (-not $Once)
