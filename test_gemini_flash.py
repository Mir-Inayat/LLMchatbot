import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key and model name
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")
print(f"API Key found: {'Yes' if api_key else 'No'}")
print(f"Using model: {model_name}")

# API endpoint based on documentation
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
print(f"Using URL: {url}")

# Request headers
headers = {"Content-Type": "application/json"}

# Request body with a simple prompt as shown in documentation
data = {
    "contents": [
        {
            "parts": [
                {"text": "Give a one-sentence response to: What is cybersecurity?"}
            ]
        }
    ]
}

# Make the API request
print("\nSending request to Gemini API...")
try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if "candidates" in result and len(result["candidates"]) > 0:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            print("\nSuccess! Response from Gemini API:")
            print(text)
            print("\nYour LLM connection is working properly!")
        else:
            print("\nAPI returned a 200 response but no content was found in the expected format.")
            print("Response:", result)
    else:
        print(f"\nAPI request failed with status code: {response.status_code}")
        print("Error details:", response.text)
        
except Exception as e:
    print(f"\nError making API request: {e}")