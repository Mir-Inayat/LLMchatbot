import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

print("=== Direct Gemini API Test ===")

if not api_key:
    print("❌ No Gemini API key found in environment variables.")
    sys.exit(1)

print(f"✅ Found Gemini API key: {api_key[:5]}...{api_key[-5:]}")

# Test API directly
model = "gemini-pro"
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

headers = {
    "Content-Type": "application/json"
}

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Say 'Connection successful' if you can read this message."
                }
            ]
        }
    ],
    "generationConfig": {
        "temperature": 0.7
    }
}

print("\nSending test request to Gemini API...")
try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise exception for 4XX/5XX status codes
    
    print(f"Response status code: {response.status_code}")
    result = response.json()
    
    print("\nResponse JSON structure:")
    print(json.dumps(result, indent=2)[:500] + "..." if len(json.dumps(result, indent=2)) > 500 else json.dumps(result, indent=2))
    
    if "candidates" in result and len(result["candidates"]) > 0:
        response_text = result["candidates"][0]["content"]["parts"][0]["text"]
        print("\nResponse text:")
        print(response_text)
        print("\n✅ API call successful!")
    else:
        print("\n❌ API call succeeded but returned no candidates.")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ API call failed: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Status code: {e.response.status_code}")
        print(f"Response body: {e.response.text}")