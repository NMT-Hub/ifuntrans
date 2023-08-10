# Script: source.ps1
$envFile = Get-Content -Path .\.env

foreach ($line in $envFile) {
    if ($line -match '^(.*?)=(.*)$') {
        $key = $matches[1]
        $value = $matches[2]
        # remove quotes
        $value = $value -replace "^\'|\'$"
        # remove double quotes
        $value = $value -replace '^"|"$'
        Set-Item -Path "env:$key" -Value $value
        echo "Setting $key to $value"
    }
}
