#!/bin/bash

# Run the Streamlit frontend for Parallel U

echo "🚀 Starting Parallel U Frontend..."
echo ""
echo "Make sure you have set up your .env.local file with:"
echo "  - MINO_API_KEY=your_api_key"
echo "  - MINO_BASE_URL=https://mino.ai (optional)"
echo ""

uv run streamlit run streamlit_app.py
