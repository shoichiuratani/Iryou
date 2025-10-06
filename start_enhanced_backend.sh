#!/bin/bash
# Enhanced Backend Startup Script
# 拡張バックエンド起動スクリプト

echo "🚀 Starting Enhanced Surgi-Motion Visualizer Backend..."
echo "🎯 Features: SAM2 Integration, Interactive ROI, Real-time Tracking"

# Change to backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing enhanced dependencies..."
pip install -r requirements_enhanced.txt

# Create necessary directories
mkdir -p static/uploads
mkdir -p static/exports
mkdir -p static/thumbnails

echo "🔧 Starting Enhanced API Server..."
echo "📡 Backend URL: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🎪 Enhanced Features: http://localhost:8000"

# Start the enhanced server
python3 enhanced_main.py