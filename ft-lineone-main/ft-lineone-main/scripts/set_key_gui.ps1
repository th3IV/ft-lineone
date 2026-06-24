Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Google AI API Key"
$form.Size = New-Object System.Drawing.Size(500,150)
$form.StartPosition = "CenterScreen"
$form.Topmost = $true

$label = New-Object System.Windows.Forms.Label
$label.Text = "Pega tu Google AI API key (AIzaSy...):"
$label.Location = New-Object System.Drawing.Point(20,20)
$label.Size = New-Object System.Drawing.Size(460,20)
$form.Controls.Add($label)

$textbox = New-Object System.Windows.Forms.TextBox
$textbox.Location = New-Object System.Drawing.Point(20,50)
$textbox.Size = New-Object System.Drawing.Size(440,30)
$form.Controls.Add($textbox)

$button = New-Object System.Windows.Forms.Button
$button.Text = "Guardar"
$button.Location = New-Object System.Drawing.Point(200,85)
$button.Size = New-Object System.Drawing.Size(100,30)
$button.Add_Click({
    $key = $textbox.Text
    if ([string]::IsNullOrWhiteSpace($key)) {
        [System.Windows.Forms.MessageBox]::Show("No ingresaste ninguna clave")
        return
    }
    $envPath = Join-Path (Get-Location) ".env"
    $content = Get-Content $envPath -Raw
    $content = $content -replace "GOOGLE_AI_API_KEY=.*", "GOOGLE_AI_API_KEY=$key"
    Set-Content $envPath -Value $content
    [System.Windows.Forms.MessageBox]::Show("API key actualizada correctamente!")
    $form.Close()
})
$form.Controls.Add($button)

$form.ShowDialog() | Out-Null
