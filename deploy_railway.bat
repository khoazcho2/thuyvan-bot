@echo off
REM Railway Deployment Script for Windows
REM Run this after installing Railway CLI

echo 1. Logging in to Railway...
railway login

echo 2. Initializing project...
railway init

echo 3. Setting BOT_TOKEN environment variable...
echo Please enter your Telegram Bot Token:
set /p BOT_TOKEN=
railway variables set BOT_TOKEN=%BOT_TOKEN%

echo 4. Deploying to Railway...
railway up

echo 5. Opening Railway dashboard...
railway open

echo Deployment complete!
pause
