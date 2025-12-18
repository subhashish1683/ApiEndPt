import os
import json                         # parse headers + pretty-print API response
import requests                     # call APIs (Swagger + Groq)
from dotenv import load_dotenv      # load .env file

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_URL = os.getenv("API_URL")
API_HEADERS = json.loads(os.getenv("API_HEADERS", "{}"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")

# Stop program early if configuration is missing
if not GROQ_API_KEY or not API_URL:
    raise RuntimeError("Missing GROQ_API_KEY or API_URL in .env")

# -----------------------------
# Fetch live API data  ------> Calls your Swagger API ----> Gets fresh live data -----> Returns stringified JSON
# -----------------------------
def fetch_api_data():
    response = requests.get(API_URL, headers=API_HEADERS, timeout=20)
    response.raise_for_status()

    if "application/json" in response.headers.get("Content-Type", ""):
        return json.dumps(response.json(), indent=2)
    return response.text
# Data flow  ----------------> Swagger API → response → JSON → string → returned


# -----------------------------
# Call Groq LLM
# -----------------------------
def call_groq(context, question):              # context : Live API response text       question : User’s question from terminal
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {                                         # Everything the LLM knows is inside this object.
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",                       # SYSTEM MESSAGE (RULES)
                "content": (
                    "You are an API assistant. "
                    "Answer the user's question ONLY using the live API data provided."
                )
            },
            {
                "role": "user",                         # USER MESSAGE (DATA + QUESTION)
                "content": f"""
API RESPONSE:
{context}

QUESTION:
{question}
"""
            }
        ],
        "temperature": 0.2
    }

    res = requests.post(url, headers=headers, json=payload, timeout=30)
    res.raise_for_status()

    return res.json()["choices"][0]["message"]["content"]

# -----------------------------
# Terminal Chat Loop
# -----------------------------
def main():
    print("\n🔥 Live API Chat (Swagger-backed)")
    print("Type 'exit' to quit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("exit", "quit"):
            break

        try:
            print("\n⏳ Fetching live API data...")
            api_data = fetch_api_data()

            print("🤖 Thinking...\n")
            answer = call_groq(api_data, question)

            print("Assistant:")
            print(answer)
            print("\n" + "-" * 60 + "\n")

        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main()


# logic : User types question ---> fetch_api_data() ------> call_groq(api_data, question) -----> print answer -----> repeat
