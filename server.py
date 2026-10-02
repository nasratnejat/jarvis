import json

from flask import Flask, request, jsonify

import pc_tasks

from config import settings
from app.ai import OpenAIProvider
from app.ai import ConversationContext


app = Flask(__name__)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

HOST = settings.HOST
PORT = settings.PORT
MODEL = settings.MODEL
OPENAI_API_KEY = settings.OPENAI_API_KEY


# --------------------------------------------------
# AI
# --------------------------------------------------

conversation = ConversationContext(
    limit=settings.HISTORY_LIMIT
)

ai_provider = OpenAIProvider(
    api_key=OPENAI_API_KEY,
    model=MODEL
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, OPTIONS"
    )

    return response


# --------------------------------------------------
# AI REQUEST
# --------------------------------------------------

def ask_openai(user_message):

    previous_messages = (
        conversation.get_messages()
    )

    reply = ai_provider.ask(
        user_message,
        previous_messages
    )

    if reply:
        conversation.add_user(
            user_message
        )

        conversation.add_assistant(
            reply
        )

    return reply


# --------------------------------------------------
# MESSAGE PROCESSING
# --------------------------------------------------

def process_message(text):

    local_result = (
        pc_tasks.run_pc_task(text)
    )

    if local_result is not None:
        return {
            "reply": local_result,
            "type": "local"
        }

    reply = ask_openai(text)

    return {
        "reply": reply,
        "type": "ai"
    }


def make_response(result):

    return jsonify({
        "ok": True,
        "reply": result["reply"],
        "response": result["reply"],
        "text": result["reply"],
        "type": result["type"],
        "state": pc_tasks.get_state()
    })


# --------------------------------------------------
# REQUEST PARSING
# --------------------------------------------------

def get_message():

    data = request.get_json(
        silent=True
    )

    if isinstance(data, dict):

        return (
            data.get("message")
            or data.get("text")
            or ""
        ).strip()

    raw = request.get_data(
        as_text=True
    )

    if raw:

        try:
            data = json.loads(raw)

            if isinstance(data, dict):

                return (
                    data.get("message")
                    or data.get("text")
                    or ""
                ).strip()

        except json.JSONDecodeError:

            return raw.strip()

    return ""


# --------------------------------------------------
# HEALTH
# --------------------------------------------------

@app.get("/health")
def health():

    return jsonify({
        "ok": True,
        "online": True,
        "model": MODEL,
        "openai_configured": bool(
            OPENAI_API_KEY
        )
    })


# --------------------------------------------------
# STATE
# --------------------------------------------------

@app.get("/state")
def state():

    return jsonify({
        "ok": True,
        "state": pc_tasks.get_state()
    })


# --------------------------------------------------
# MEMORY
# --------------------------------------------------

@app.get("/memory")
def memory():

    return jsonify({
        "ok": True,
        "memory": conversation.get_recent(10)
    })


# --------------------------------------------------
# RESET
# --------------------------------------------------

@app.post("/reset")
def reset():

    conversation.clear()

    return jsonify({
        "ok": True,
        "reply": "Conversation reset, Sir."
    })


# --------------------------------------------------
# CHAT
# --------------------------------------------------

@app.post("/chat")
def chat():

    text = get_message()

    if not text:

        return jsonify({
            "ok": False,
            "reply": (
                "Please give me something "
                "to work with, Sir."
            )
        }), 400

    print(
        f"[JARVIS] Message: {text}"
    )

    try:

        result = process_message(text)

        print(
            f"[JARVIS] Response type: "
            f"{result['type']}"
        )

        return make_response(result)

    except Exception as e:

        print(
            "[CHAT ERROR]",
            repr(e)
        )

        return jsonify({
            "ok": False,
            "reply": (
                f"I encountered an error, Sir: {e}"
            )
        }), 500


# --------------------------------------------------
# STREAM
# --------------------------------------------------

@app.post("/stream")
def stream():

    text = get_message()

    if not text:

        return jsonify({
            "ok": False,
            "reply": (
                "Please give me something "
                "to work with, Sir."
            )
        }), 400

    print(
        f"[JARVIS] Message: {text}"
    )

    try:

        result = process_message(text)

        print(
            f"[JARVIS] Response type: "
            f"{result['type']}"
        )

        return make_response(result)

    except Exception as e:

        print(
            "[STREAM ERROR]",
            repr(e)
        )

        return jsonify({
            "ok": False,
            "reply": (
                f"I encountered an error, Sir: {e}"
            )
        }), 500


# --------------------------------------------------
# OPTIONS / CORS
# --------------------------------------------------

@app.route(
    "/stream",
    methods=["OPTIONS"]
)
def stream_options():

    return "", 204


@app.route(
    "/chat",
    methods=["OPTIONS"]
)
def chat_options():

    return "", 204


@app.route(
    "/reset",
    methods=["OPTIONS"]
)
def reset_options():

    return "", 204


# --------------------------------------------------
# ERROR HANDLERS
# --------------------------------------------------

@app.errorhandler(404)
def not_found(_):

    return jsonify({
        "ok": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):

    print(
        "[FLASK 500]",
        repr(error)
    )

    return jsonify({
        "ok": False,
        "error": str(error)
    }), 500


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":

    print()
    print("=" * 55)
    print("J.A.R.V.I.S. — AI MODULE")
    print("=" * 55)

    print(
        f"Server : http://{HOST}:{PORT}"
    )

    print(
        f"Model  : {MODEL}"
    )

    if OPENAI_API_KEY:
        print("OpenAI : configured")
    else:
        print("OpenAI : MISSING API KEY")

    print("=" * 55)
    print()

    app.run(
        host=HOST,
        port=PORT,
        debug=settings.DEBUG,
        threaded=True
    )