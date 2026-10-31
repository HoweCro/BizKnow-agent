# PowerShell 启动脚本。

Write-Host "AI Customer Support Chatbot Launcher" -ForegroundColor Green

$root = $PSScriptRoot
$server = Join-Path $root "server"
$client = Join-Path $root "client"

Write-Host "1) Backend only"
Write-Host "2) client only"
Write-Host "3) Both (two windows)"
$choice = Read-Host "Enter number (1-3)"

switch ($choice) {
    "1" {
         Set-Location $server
    & ".\.venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8000
    }
    "2" {
        Set-Location $client
        npm run dev
    }
    "3" {
        Write-Host "Launching two windows..." -ForegroundColor Yellow
        Start-Process powershell -ArgumentList "-NoExit -Command `"Set-Location '$server'; & '.\.venv\Scripts\python.exe' -m uvicorn main:app --reload --port 8000`""
        Start-Process powershell -ArgumentList "-NoExit -Command cd '$client'; npm run dev"
    }
    default {
        Write-Host "Invalid choice" -ForegroundColor Red
    }
}
