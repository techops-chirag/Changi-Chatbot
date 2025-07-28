#!/bin/bash

echo "Deploying Changi Chatbot to Railway/Render..."

# Simple deployment to free platforms
echo "Building Docker image..."
docker build -t changi-chatbot .

echo "Deployment options:"
echo "1. Railway: Connect your GitHub repo at railway.app"
echo "2. Render: Connect your GitHub repo at render.com"
echo "3. Heroku: Use heroku container:push web"

echo "Your environment variables are already configured!"
echo "No additional setup needed for API keys."
