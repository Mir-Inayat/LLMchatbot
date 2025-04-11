import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")

# Try a different approach - first list available models
list_models_url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"

print(f"Checking available models...")
try:
    response = requests.get(list_models_url)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        models = response.json()
        print("\nAvailable models:")
        for model in models.get('models', []):
            print(f"- {model.get('name')}")
            
        # Now try the correct model name from the list
        if models.get('models'):
            # Get the first gemini model from the list
            gemini_models = [m for m in models.get('models', []) if 'gemini' in m.get('name', '').lower()]
            
            if gemini_models:
                model_name = gemini_models[0].get('name')
                print(f"\nTrying with model: {model_name}")
                
                # Extract just the model name part
                if '/' in model_name:
                    model_name = model_name.split('/')[-1]
                
                url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
                
                headers = {"Content-Type": "application/json"}
                data = {
                    "contents": [
                        {
                            "parts": [
                                {"text": "Give a one-sentence response to: What is cybersecurity?"}
                            ]
                        }
                    ]
                }
                
                print(f"Sending request to: {url}")
                response = requests.post(url, headers=headers, json=data)
                print(f"Status code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if "candidates" in result and len(result["candidates"]) > 0:
                        text = result["candidates"][0]["content"]["parts"][0]["text"]
                        print("\nSuccess! Response from Gemini API:")
                        print(text)
                    else:
                        print("\nAPI returned a 200 response but no content was found.")
                else:
                    print(f"API request failed with: {response.text}")
            else:
                print("No Gemini models found.")
        else:
            print("No models returned from API.")
    else:
        print(f"Failed to list models: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")