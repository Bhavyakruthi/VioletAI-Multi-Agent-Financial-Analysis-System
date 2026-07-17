import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_cohere():
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        print("COHERE_API_KEY not found")
        return

    print(f"Testing Cohere API with key: {api_key[:5]}...{api_key[-5:]}")
    
    url = "https://api.cohere.ai/v1/generate"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}"
    }
    payload = {
        "max_tokens": 10,
        "truncate": "END",
        "return_likelihoods": "NONE",
        "prompt": "Hello",
        "model": "command"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Cohere API test SUCCESS")
        else:
            print(f"Cohere API test FAILED: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error testing Cohere: {e}")

if __name__ == "__main__":
    test_cohere()
