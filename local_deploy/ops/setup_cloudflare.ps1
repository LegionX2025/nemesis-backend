Write-Host "========================================================"
Write-Host "LIONSGATE NEMESIS - CLOUDFLARE INFRASTRUCTURE PROVISIONING"
Write-Host "========================================================"
Write-Host "Please ensure you have run 'npx wrangler login' before running this script."
Write-Host "This script will output IDs that you MUST copy into your wrangler.toml file."
Write-Host ""

Write-Host "--- KV Namespaces ---"
npx wrangler kv:namespace create NEMESIS_CACHE
npx wrangler kv:namespace create ENTITY_CACHE
npx wrangler kv:namespace create SESSION_CACHE
npx wrangler kv:namespace create TOKEN_CACHE
npx wrangler kv:namespace create OSINT_CACHE
Write-Host ""

Write-Host "--- D1 Database ---"
npx wrangler d1 create nemesis
Write-Host ""

Write-Host "--- R2 Buckets ---"
npx wrangler r2 bucket create nemesis-reports
npx wrangler r2 bucket create nemesis-evidence
npx wrangler r2 bucket create nemesis-screenshots
npx wrangler r2 bucket create nemesis-exports
Write-Host ""

Write-Host "--- Message Queues ---"
npx wrangler queues create wallet-tracing
npx wrangler queues create entity-resolution
npx wrangler queues create gemini-analysis
npx wrangler queues create report-generation
npx wrangler queues create notifications
Write-Host ""

Write-Host "========================================================"
Write-Host "PROVISIONING COMPLETE."
Write-Host "Please look through the output above and copy the generated IDs into:"
Write-Host "frontend/nemesis-global-worker/wrangler.toml"
Write-Host "========================================================"
pause
