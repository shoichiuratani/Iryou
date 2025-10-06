#!/bin/bash
# Enhanced Frontend Startup Script
# 拡張フロントエンド起動スクリプト

echo "🚀 Starting Enhanced Surgi-Motion Visualizer Frontend..."
echo "🎯 Features: Interactive ROI Selection, Real-time Tracking UI"

# Change to frontend directory
cd "$(dirname "$0")/frontend/public"

# Check if enhanced_index.html exists
if [ ! -f "enhanced_index.html" ]; then
    echo "❌ Error: enhanced_index.html not found!"
    exit 1
fi

# Backup original index.html and replace with enhanced version
if [ -f "index.html" ]; then
    cp index.html index_original_backup.html
    echo "📄 Backed up original index.html"
fi

cp enhanced_index.html index.html
echo "🔄 Switched to enhanced UI"

echo "🌐 Starting HTTP Server..."
echo "📡 Frontend URL: http://localhost:3000"
echo "🎮 Enhanced ROI Selection Interface available"

# Start Python HTTP server
python3 -m http.server 3000