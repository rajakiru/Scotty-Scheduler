#!/bin/bash

# Scotty Scheduler - Setup Script
# This script automates the setup process for the project

set -e  # Exit on error

echo "=================================================="
echo "  Scotty Scheduler - Setup Script"
echo "  Winner - Google Deepmind AI Agents Hackathon"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Found Python $python_version"
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"
echo ""

# Setup environment variables
if [ ! -f ".env" ]; then
    echo "Setting up environment variables..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Please edit .env and add your OPENAI_API_KEY"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Extract data files if they exist
echo "Checking for data files..."

if [ -f "stored_index.zip" ] && [ ! -d "index_data" ]; then
    echo "Extracting stored_index.zip..."
    unzip -q stored_index.zip
    # Rename if extracted as 'stored_index' instead of 'index_data'
    if [ -d "stored_index" ] && [ ! -d "index_data" ]; then
        mv stored_index index_data
    fi
    echo "✓ Vector index extracted to index_data/"
elif [ -d "index_data" ]; then
    echo "✓ Vector index already extracted"
else
    echo "⚠️  Warning: stored_index.zip not found. You'll need to build the index."
fi
echo ""

if [ -f "syllabi_pdfs_fall2024ECE.zip" ] && [ ! -d "syllabi_pdfs_fall2024ECE" ]; then
    echo "Extracting Fall 2024 syllabi (this may take a moment)..."
    unzip -q syllabi_pdfs_fall2024ECE.zip
    echo "✓ Fall 2024 syllabi extracted"
elif [ -d "syllabi_pdfs_fall2024ECE" ]; then
    echo "✓ Fall 2024 syllabi already extracted"
fi

if [ -f "syllabi_pdfs_spring2025ECE.zip" ] && [ ! -d "syllabi_pdfs_spring2025ECE" ]; then
    echo "Extracting Spring 2025 syllabi (this may take a moment)..."
    unzip -q syllabi_pdfs_spring2025ECE.zip
    echo "✓ Spring 2025 syllabi extracted"
elif [ -d "syllabi_pdfs_spring2025ECE" ]; then
    echo "✓ Spring 2025 syllabi already extracted"
fi

echo ""
echo "=================================================="
echo "  Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file and add your OPENAI_API_KEY:"
echo "   nano .env"
echo ""
echo "2. Start the backend server (Terminal 1):"
echo "   source venv/bin/activate"
echo "   python inference.py"
echo ""
echo "3. Start the frontend (Terminal 2):"
echo "   source venv/bin/activate"
echo "   streamlit run home.py"
echo ""
echo "4. Open http://localhost:8501 in your browser"
echo ""
echo "=================================================="
