import json
import urllib.error
import urllib.request

from app.ai.provider import AIProvider
from app.ai.prompts import SYSTEM_PROMPT


class OpenAIProvider(AIProvider):

    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def ask(self, user_message, conversation=None):

        if not self.api_key:
            return (
                "My OpenAI API key is not configured, Sir. "
                "Please check your .env file."
            )

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        if conversation:
            messages.extend(
                conversation
            )

        messages.append({
            "role": "user",
            "content": user_message
        })

        payload = {
            "model": self.model,
            "messages": messages
        }

        body = json.dumps(
            payload
        ).encode("utf-8")

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": (
                    f"Bearer {self.api_key}"
                )
            },
            method="POST"
        )

        try:
            print("[JARVIS] Contacting OpenAI...")

            with urllib.request.urlopen(
                req,
                timeout=30
            ) as response:
                raw = (
                    response
                    .read()
                    .decode("utf-8")
                )

            data = json.loads(raw)

            reply = (
                data
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )

            if not reply:
                print("[OPENAI] Empty response")
                return (
                    "I received an empty response, Sir."
                )

            print(
                "[JARVIS] OpenAI response received."
            )

            return reply

        except urllib.error.HTTPError as e:

            try:
                raw_error = (
                    e.read()
                    .decode("utf-8")
                )

                error_data = json.loads(
                    raw_error
                )

                message = (
                    error_data
                    .get("error", {})
                    .get("message")
                )

                if message:
                    print(
                        "[OPENAI HTTP ERROR]",
                        message
                    )

                    return (
                        f"OpenAI error: {message}"
                    )

            except Exception:
                pass

            print(
                "[OPENAI HTTP ERROR]",
                repr(e)
            )

            return (
                f"OpenAI returned HTTP error "
                f"{e.code}, Sir."
            )

        except urllib.error.URLError as e:

            print(
                "[OPENAI CONNECTION ERROR]",
                repr(e)
            )

            return (
                "I couldn't connect to OpenAI, Sir. "
                "Please check your internet connection."
            )

        except Exception as e:

            print(
                "[OPENAI ERROR]",
                repr(e)
            )

            return (
                f"I encountered an OpenAI error, Sir: {e}"
            )