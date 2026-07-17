import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def list_models():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY not found")
        return

    genai.configure(api_key=api_key)
    
    print("Listing available models with 'flash':")
    try:
        found = False
        for m in genai.list_models():
            if 'flash' in m.name.lower():
                print(f"FOUND_MODEL: {m.name}")
                found = True
        if not found:
            print("No flash models found. Listing ALL available models:")
            for m in genai.list_models():
                print(f"FOUND_MODEL: {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
