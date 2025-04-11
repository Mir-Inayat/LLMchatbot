import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
result_file = "llm_test_results_updated.txt"

with open(result_file, "w") as f:
    f.write(f"API Key found: {'Yes' if api_key else 'No'}\n")

    # Using the updated API endpoint format (v1 instead of v1beta)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}"
    f.write(f"Using API URL: {url}\n")

    # Request headers
    headers = {"Content-Type": "application/json"}

    # Request body with a simple prompt
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
    f.write("Sending request to Gemini API...\n")
    try:
        response = requests.post(url, headers=headers, json=data)
        f.write(f"Status code: {response.status_code}\n")
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                f.write("\nSuccess! Response from Gemini API:\n")
                f.write(text + "\n")
                f.write("\nYour LLM connection is working properly!\n")
            else:
                f.write("\nAPI returned a 200 response but no content was found in the expected format.\n")
                f.write(f"Response: {result}\n")
        else:
            f.write(f"\nAPI request failed with status code: {response.status_code}\n")
            f.write(f"Error details: {response.text}\n")
            
    except Exception as e:
        f.write(f"\nError making API request: {e}\n")

print(f"Test completed. Results saved to {result_file}")