import os
import json
import requests
from dotenv import load_dotenv

# =====================================================
# LOAD ENVIRONMENT VARIABLES
# =====================================================
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")

API_URL = os.getenv("API_URL")
API_HEADERS = json.loads(os.getenv("API_HEADERS", "{}"))

if not GROQ_API_KEY or not API_URL:
    raise RuntimeError("❌ Missing required environment variables")

# =====================================================
# MCP SERVER (Tool Provider)
# This is your MCP Server exposing ONE TOOL
# =====================================================
def mcp_server_fetch():
    """
    MCP TOOL: get_live_api_data
    Fetches live data from API every time it is called
    """
    response = requests.get(
        API_URL,
        headers=API_HEADERS,
        timeout=20
    )
    response.raise_for_status()

    if "application/json" in response.headers.get("Content-Type", ""):
        return json.dumps(response.json(), indent=2)

    return response.text


# =====================================================
# MCP CLIENT (Model Tool Caller)
# =====================================================
def call_groq_with_mcp(tool_data, user_question):               # tool_data = recieved from 'mcp_server_fetch()'
    """
    MCP Client:
    - Sends tool output as context
    - Model reasons ONLY over tool output
    """

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an MCP-based assistant.\n"
                    "You MUST answer using ONLY the tool data provided.\n"
                    "If the answer is not present, say: 'Data not available.'"
                )
            },
            {
                "role": "user",
                "content": f"""
MCP TOOL RESULT (get_live_api_data):
{tool_data}

USER QUESTION:
{user_question}
"""
            }
        ]
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# =====================================================
# MCP HOST (Chat Application)
# =====================================================
def main():
    print("\n🔥 MCP Live API Chatbot")
    print("🔌 Tool: get_live_api_data")
    print("Type 'exit' to quit\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("exit", "quit"):
            break

        try:
            print("\n⏳ MCP Server: Fetching live data...")
            tool_data = mcp_server_fetch()

            print("🤖 MCP Client: Reasoning...\n")
            answer = call_groq_with_mcp(tool_data, question)

            print("Assistant:")
            print(answer)
            print("\n" + "-" * 60)

        except Exception as e:
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
