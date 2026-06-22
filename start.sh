#!/bin/bash
# Quick start script for Industrial Safety Intelligence Platform

echo "🏭 Industrial Safety Intelligence Platform"
echo "==========================================\n"

# Check API key
if [ -z "$OPENROUTER_API_KEY" ]; then
  echo "⚠️  WARNING: OPENROUTER_API_KEY not set."
  echo "   Set it with: export OPENROUTER_API_KEY='sk-or-v1-your-key'"
  echo "   AI analysis features will not work without it.\n"
fi

# Install deps
echo "📦 Installing dependencies..."
cd backend && pip install -r requirements.txt -q

# Regenerate data (optional)
echo "📊 Generating datasets..."
cd ../data && python3 generate_dataset.py

# Start backend
echo "\n🚀 Starting backend on http://localhost:8000"
echo "📂 Open frontend/index.html in your browser"
echo "📖 API docs at http://localhost:8000/docs\n"
cd ../backend && uvicorn main:app --reload --port 8000
