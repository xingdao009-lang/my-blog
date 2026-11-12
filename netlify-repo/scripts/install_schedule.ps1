param(
    [string]$Time = "08:30"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Bat = Join-Path $Root "update_news.bat"
$TaskName = "TaxAI-News-Update"

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$Bat`" --no-pause" -WorkingDirectory $Root
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily public tax and finance news update" -Force

Write-Host "Scheduled task created: $TaskName"
Write-Host "Run time: $Time daily"
