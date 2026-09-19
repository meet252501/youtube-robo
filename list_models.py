import os
from google import genai
from dotenv import load_dotenv

def main():
    load_dotenv()
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    for m in client.models.list():
        print(m.name)

if __name__ == "__main__":
    main()
