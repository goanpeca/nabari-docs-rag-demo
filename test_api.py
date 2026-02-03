#!/usr/bin/env python3
"""
Quick test to verify Anthropic API key and available models.
"""

import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print(" No API key found in .env file")
    exit(1)

print(f" API key found (starts with: {api_key[:10]}...)")

# Test the API with different models (NEW Claude 4.x naming convention)
models_to_test = [
    "claude-sonnet-4-20250514",  # Claude Sonnet 4 (May 2025) - LATEST
    "claude-opus-4-20250514",  # Claude Opus 4.5 (May 2025)
    "claude-3-7-sonnet-20250219",  # Claude 3.7 Sonnet (Feb 2025)
    "claude-3-5-sonnet-20241022",  # Claude 3.5 Sonnet (Oct 2024) - OLD
    "claude-3-haiku-20240307",  # Claude 3 Haiku (Mar 2024)
]

client = Anthropic(api_key=api_key)

print("\n🧪 Testing models...\n")

for model in models_to_test:
    try:
        response = client.messages.create(
            model=model, max_tokens=10, messages=[{"role": "user", "content": "Hi"}]
        )
        print(f" {model} - WORKS!")
        print(f"   Response: {response.content[0].text}")
        break  # Found a working model
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not_found" in error_msg:
            print(f" {model} - Not available")
        elif "401" in error_msg or "authentication" in error_msg.lower():
            print(" API key authentication failed!")
            print(f"   Error: {e}")
            break
        else:
            print(f" {model} - Error: {error_msg[:100]}")

print("\n" + "=" * 50)
print("RESULTS SUMMARY")
print("=" * 50)
print("\nIf ALL models failed:")
print("- Your API key might be invalid")
print("- Check your tier at: https://console.anthropic.com/settings/limits")
print("\nIf only some models work:")
print("- Tier 1: Only Haiku 3.x available")
print("- Tier 2: Haiku 3.x + Sonnet 3.7 + Sonnet 4.x + Opus 4.x ")
print("- Tier 3+: All models including Claude 4.5")
print("\nNew models (2025):")
print("- claude-sonnet-4-20250514 (recommended)")
print("- claude-opus-4-20250514 (highest quality)")
print("- claude-3-7-sonnet-20250219 (good balance)")
