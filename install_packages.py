#!/usr/bin/env python3
"""Install required packages with user flag to avoid permission issues"""
import subprocess
import sys

packages = [
    "llama-index",
    "llama-index-llms-gemini", 
    "llama-index-embeddings-gemini",
    "falkordb"
]

for package in packages:
    print(f"Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", package])
        print(f"✓ {package} installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")

print("\nInstallation complete. Please restart your Python environment before running graph_rag_bridge.py")
