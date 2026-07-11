@echo off
echo ========================================================
echo LIONSGATE NEMESIS - CLOUDFLARE INFRASTRUCTURE PROVISIONING
echo ========================================================
echo Please ensure you have run 'npx wrangler login' before running this script.
echo This script will output IDs that you MUST copy into your wrangler.toml file.
echo.

echo --- KV Namespaces ---
call npx wrangler kv:namespace create NEMESIS_CACHE
call npx wrangler kv:namespace create ENTITY_CACHE
call npx wrangler kv:namespace create SESSION_CACHE
call npx wrangler kv:namespace create TOKEN_CACHE
call npx wrangler kv:namespace create OSINT_CACHE
echo.

echo --- D1 Database ---
call npx wrangler d1 create nemesis
echo.

echo --- R2 Buckets ---
call npx wrangler r2 bucket create nemesis-reports
call npx wrangler r2 bucket create nemesis-evidence
call npx wrangler r2 bucket create nemesis-screenshots
call npx wrangler r2 bucket create nemesis-exports
echo.

echo --- Message Queues ---
call npx wrangler queues create wallet-tracing
call npx wrangler queues create entity-resolution
call npx wrangler queues create gemini-analysis
call npx wrangler queues create report-generation
call npx wrangler queues create notifications
echo.

echo ========================================================
echo PROVISIONING COMPLETE.
echo Please look through the output above and copy the generated IDs into:
echo frontend\nemesis-global-worker\wrangler.toml
echo ========================================================
pause
