import os
import json
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is not configured")


client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(
        timeout=10000
    )
)


ALLOWED_DEPARTMENTS = {
    "computer-science",
    "information-technology",
    "ece",
    "mechanical",
    "faculty",
    "administration"
}


def interpret_intent(user_intent: str):

    prompt = f"""
You are an AI assistant for an Intent-Based Campus Network Management System.

Interpret the user's request and identify:

1. Source department
2. Destination department
3. Required network action

Allowed departments:
- computer-science
- information-technology
- ece
- mechanical
- faculty
- administration

Department name mappings:
- Computer Science, CS, students, student network -> computer-science
- Information Technology, IT -> information-technology
- Electronics and Communication, ECE -> ece
- Mechanical Engineering, Mechanical -> mechanical
- Faculty, teachers, staff -> faculty
- Administration, admin -> administration

Allowed actions:
- allow
- block

Action mappings:
- restrict, prevent, deny, block -> block
- permit, allow, restore, enable -> allow

Return only valid JSON in this format:
{{"source":"computer-science","destination":"administration","action":"block"}}

If the request is unclear or does not identify a valid
source, destination, and action, return:
{{"error":"Unable to understand the network intent"}}

User request: {user_intent}
"""

    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0
                )
            )

            result = json.loads(response.text)

            if "error" in result:
                raise ValueError(result["error"])

            source = result.get("source")
            destination = result.get("destination")
            action = result.get("action")

            if (
                source not in ALLOWED_DEPARTMENTS
                or destination not in ALLOWED_DEPARTMENTS
                or action not in {"allow", "block"}
            ):
                raise ValueError(
                    "Gemini returned unsupported network parameters"
                )

            return {
                "source": source,
                "destination": destination,
                "action": action
            }

        except Exception as e:

            if attempt == 0 and (
                "503" in str(e) or "UNAVAILABLE" in str(e)
            ):
                time.sleep(2)
                continue

            raise RuntimeError(
                "Gemini intent interpretation failed: " + str(e)
            )
