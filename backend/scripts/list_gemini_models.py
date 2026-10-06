import os
import sys

from google import genai


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    print("Available Gemini models supporting content generation:")
    try:
        for model in client.models.list():
            actions = getattr(model, "supported_actions", []) or []
            if "generateContent" in actions or "generate_content" in actions or not actions:
                print(f" - {model.name}")
    except Exception as e:
        print(f"Failed to list models: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
