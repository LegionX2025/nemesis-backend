# deploy_secrets.ps1
# Parses the root .env file and deploys relevant API keys and URIs to the Cloudflare Worker

$envPath = "..\..\.env"

if (-Not (Test-Path $envPath)) {
    Write-Host "Error: .env file not found at $envPath" -ForegroundColor Red
    exit 1
}

Write-Host "Parsing .env for Cloudflare Secrets..." -ForegroundColor Cyan

# Keywords to match for secrets
$secretKeywords = @("_KEY", "_TOKEN", "_URI", "MONGO_URL", "INFURA_", "GETBLOCK_", "PUBLICNODE_", "SOLANA_RPC")

$lines = Get-Content $envPath
$count = 0

foreach ($line in $lines) {
    $line = $line.Trim()
    
    # Skip comments and empty lines
    if ($line.StartsWith("#") -or $line -eq "") { continue }
    
    if ($line.Contains("=")) {
        $parts = $line -split '=', 2
        $key = $parts[0].Trim()
        $value = $parts[1].Trim()

        # Remove surrounding quotes if they exist
        if ($value.StartsWith('"') -and $value.EndsWith('"')) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        # Check if key matches our target keywords
        $isSecret = $false
        foreach ($keyword in $secretKeywords) {
            if ($key.Contains($keyword)) {
                $isSecret = $true
                break
            }
        }

        if ($isSecret) {
            Write-Host "Deploying Secret: $key" -ForegroundColor Yellow
            # Pipe value into wrangler secret put
            $value | npx wrangler secret put $key
            $count++
        }
    }
}

Write-Host "`nSuccessfully deployed $count secrets to Cloudflare!" -ForegroundColor Green
