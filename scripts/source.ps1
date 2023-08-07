# Script: source.ps1
$envFile = Get-Content -Path .\.env

foreach ($line in $envFile) {
    if ($line -match '^export (.*?)=(.*)$') {
        $key = $matches[1]
        $value = $matches[2]
        Set-Item -Path "env:$key" -Value $value
        echo "Setting $key to $value"
    }
}
