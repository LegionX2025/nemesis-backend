@echo off
set CI=true
echo 🚀 Attempting deployment with standard npx wrangler...
del pylock.toml 2>nul
npx wrangler deploy
pause
