import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key and model name from env
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.0-pro")

# Output file
result_file = "gemini_test_final.txt"

with open(result_file, "w") as f:
    f.write(f"Testing Gemini API Connection\n")
    f.write(f"===========================\n\n")
    f.write(f"API Key: {api_key[:5]}...{api_key[-4:]}\n")
    f.write(f"Model: {model_name}\n\n")
    
    # Try different models and API versions to find what works
    models_to_try = [
        {"name": "gemini-1.0-pro", "version": "v1beta"},
        {"name": "gemini-1.0-pro", "version": "v1"},
        {"name": "gemini-pro", "version": "v1beta"},
        {"name": "gemini-pro", "version": "v1"},
        {"name": "gemini-1.5-pro", "version": "v1beta"},
        {"name": "gemini-1.5-flash", "version": "v1beta"},
        {"name": model_name, "version": "v1beta"},
    ]
    
    for test_model in models_to_try:
        model = test_model["name"]
        version = test_model["version"]
        
        f.write(f"\n\nTrying {model} with {version} API...\n")
        
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={api_key}"
        f.write(f"URL: {url}\n")
        
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": "Give a one-sentence response about cybersecurity."}
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            f.write(f"Status code: {response.status_code}\n")
            
            if response.status_code == 200:
                result = response.json()
                f.write("Response structure: " + json.dumps(result.keys(), indent=2) + "\n")
                
                if "candidates" in result and len(result["candidates"]) > 0:
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    f.write("\n✅ SUCCESS! Response:\n")
                    f.write(text + "\n")
                else:
                    f.write("❌ No candidates in response\n")
                    f.write("Response: " + json.dumps(result, indent=2) + "\n")
            else:
                f.write("❌ Request failed\n")
                f.write("Error: " + response.text + "\n")
                
        except Exception as e:
            f.write(f"❌ Exception: {str(e)}\n")

print(f"Test completed. Results saved to {result_file}")