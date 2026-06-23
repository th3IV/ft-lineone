Write-Host "Pega tu Google AI API key (AIzaSy...) y presiona Enter:"
$key = Read-Host
if ([string]::IsNullOrWhiteSpace($key)) {
    Write-Host "ERROR: No ingresaste ninguna clave"
    exit 1
}
$envPath = Join-Path (Get-Location) ".env"
$content = Get-Content $envPath -Raw
$content = $content -replace "GOOGLE_AI_API_KEY=.*", "GOOGLE_AI_API_KEY=$key"
Set-Content $envPath -Value $content
Write-Host "OK! GOOGLE_AI_API_KEY actualizada correctamente"
