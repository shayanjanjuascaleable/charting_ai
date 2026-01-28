#!/bin/bash
# Build script for React frontend

echo "Building React frontend..."
cd frontend
npm install
npm run build
echo "Build complete! Output in frontend/dist/"
cd ..

