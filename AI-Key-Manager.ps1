param()

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   AI SWARM KEY MANAGER (OPENROUTER & ZEN)   " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$settingsPath = "$env:USERPROFILE\.claude\settings.json"

if (-not (Test-Path $settingsPath)) {
    Write-Host "[ERROR] Claude settings.json not found." -ForegroundColor Red
    exit 1
}

$settings = Get-Content $settingsPath | ConvertFrom-Json
$currentKey = $settings.env.ANTHROPIC_AUTH_TOKEN

Write-Host "[+] Testing current OpenRouter API Key..." -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer $currentKey"
    "HTTP-Referer" = "https://localhost"
    "X-Title" = "AI Swarm Watchdog"
}

try {
    $response = Invoke-RestMethod -Uri "https://openrouter.ai/api/v1/auth/key" -Method Get -Headers $headers
    Write-Host "[SUCCESS] OpenRouter API Key is valid and active!" -ForegroundColor Green
    Write-Host "Key Label: $($response.data.label)" -ForegroundColor Green
    Write-Host "Balance / Limit: $($response.data.usage) / $($response.data.limit)" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] API Key check failed! The key may be expired or invalid." -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
    
    $newKey = Read-Host "`n[ACTION REQUIRED] Please generate a new OpenRouter key at https://openrouter.ai/keys and paste it here"
    
    if (-not [string]::IsNullOrWhiteSpace($newKey)) {
        $settings.env.ANTHROPIC_AUTH_TOKEN = $newKey.Trim()
        $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath
        Write-Host "[+] New key saved! Re-run this script to verify." -ForegroundColor Green
    } else {
        Write-Host "[-] No key entered. Exiting." -ForegroundColor Yellow
    }
}

Write-Host "`n[+] Diagnostics complete." -ForegroundColor Cyan
