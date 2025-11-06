#!/bin/bash
# Quick start script for Smart Task Allocator

echo "🚀 Smart Task Allocator - Quick Start"
echo "======================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Start the service
echo ""
echo "🌟 Starting Smart Task Allocator service..."
echo "   API will be available at: http://localhost:8000"
echo "   API docs at: http://localhost:8000/docs"
echo ""
python main.py
