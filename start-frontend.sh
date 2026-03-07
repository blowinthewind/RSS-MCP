#!/bin/bash
# Start frontend dev server

set -e  # Exit on error

echo "Starting RSS MCP Frontend..."

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "Error: frontend directory not found."
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install Node.js first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Change to frontend directory
cd frontend

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the dev server
echo "Starting dev server..."
npm run dev
