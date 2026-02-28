# Railway Deployment Script
# Run this after installing Railway CLI

# 1. Login to Railway
railway login

# 2. Initialize project (select your Railway team/project)
railway init

# 3. Set environment variables
railway variables set BOT_TOKEN=your_telegram_bot_token_here

# 4. Deploy to Railway
railway up

# 5. Open the deployed project
railway open
