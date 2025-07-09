#!/bin/bash

# FleetPulse Ollama Setup Script
# This script helps you download and set up models for the included Ollama service

set -e

echo "🚀 FleetPulse Ollama Setup"
echo "=========================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Ollama container is running
if ! docker ps | grep -q fleetpulse-ollama; then
    echo "❌ FleetPulse Ollama container is not running."
    echo "   Please start the services first: docker-compose up -d"
    exit 1
fi

echo "✅ Ollama container is running"

# Function to download a model
download_model() {
    local model=$1
    local description=$2
    
    echo ""
    echo "📥 Downloading $model ($description)..."
    echo "   This may take several minutes depending on your internet connection."
    
    if docker exec fleetpulse-ollama ollama pull "$model"; then
        echo "✅ Successfully downloaded $model"
    else
        echo "❌ Failed to download $model"
        return 1
    fi
}

# List available models
echo ""
echo "Available models to download:"
echo "1. phi3:mini        - Microsoft Phi-3 Mini (Ultra lightweight, ~2.3GB) ⭐ RECOMMENDED FOR DEV"
echo "2. llama3.2:1b      - Llama 3.2 1B (Tiny but capable, ~1.3GB) ⚡ FASTEST"
echo "3. tinyllama:1.1b   - TinyLlama (Extremely small, ~0.6GB) 🪶 MINIMAL"
echo "4. llama3.1:8b      - Meta's Llama 3.1 8B (Full featured, ~4.7GB)"
echo "5. mistral:7b       - Mistral 7B (Good performance, ~4.1GB)"  
echo "6. codellama:7b     - Code Llama 7B (Code tasks, ~3.8GB)"
echo "7. Dev lightweight  - Download phi3:mini + tinyllama (best for development)"
echo "8. Custom model     - Enter your own model name"
echo "9. Skip             - Exit without downloading"

echo ""
read -p "Choose an option (1-9): " choice

case $choice in
    1)
        download_model "phi3:mini" "Microsoft Phi-3 Mini - Excellent for development, fast responses"
        ;;
    2)
        download_model "llama3.2:1b" "Llama 3.2 1B - Tiny but surprisingly capable"
        ;;
    3)
        download_model "tinyllama:1.1b" "TinyLlama - Minimal resource usage"
        ;;
    4)
        download_model "llama3.1:8b" "Meta's Llama 3.1 8B - Excellent general purpose model"
        ;;
    5)
        download_model "mistral:7b" "Mistral 7B - Fast and efficient"
        ;;
    6)
        download_model "codellama:7b-instruct" "Code Llama 7B Instruct - Specialized for coding tasks"
        ;;
    7)
        echo "📦 Downloading development-friendly models..."
        download_model "phi3:mini" "Primary development model"
        download_model "tinyllama:1.1b" "Backup ultra-fast model"
        ;;
    8)
        echo ""
        read -p "Enter custom model name (e.g., llama3.1:70b): " custom_model
        if [[ -n "$custom_model" ]]; then
            download_model "$custom_model" "Custom model"
        else
            echo "❌ No model name provided"
            exit 1
        fi
        ;;
    9)
        echo "⏭️  Skipping model download"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

# Check downloaded models
echo ""
echo "📋 Currently available models:"
docker exec fleetpulse-ollama ollama list

echo ""
echo "🎉 Setup complete!"
echo ""
echo "You can now:"
echo "- Access FleetPulse UI: http://localhost:8080"
echo "- Use MCP queries: http://localhost:8001/mcp/v1/query"
echo "- Test Ollama directly: http://localhost:11434"
echo ""
echo "Example FleetPulse query:"
echo 'curl -X POST http://localhost:8001/mcp/v1/query \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d '\''{"context":{"data":"How many hosts are in my fleet?"}}'\'
echo ""
echo "Example direct Ollama chat:"
echo 'curl http://localhost:11434/api/chat -d '\''{'
echo '  "model": "phi3:mini",'
echo '  "messages": [{"role": "user", "content": "Hello!"}]'
echo '}'\'
