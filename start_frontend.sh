#!/bin/bash

# フロントエンド簡単起動スクリプト

echo "🚀 Starting Surgi-Motion Visualizer Frontend..."

cd /home/user/webapp/frontend/public

echo "📡 Frontend will be available at: http://localhost:3000"
echo "🛑 Stop with Ctrl+C"
echo ""

# Python HTTP server for frontend
python3 -m http.server 3000