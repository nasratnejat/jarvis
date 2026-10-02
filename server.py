import json

from flask import Flask, request, jsonify

import pc_tasks

from config import settings
from app.ai import OpenAIProvider
from app.ai import ConversationContext
from app.ai.agent import JarvisAgent
from app.commands.timers import timer_manager


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
    model=MODEL,
)

agent = JarvisAgent(
    provider=ai_provider,
    conversation=conversation,
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

@app.after_request
def add_cors_headers(response):

    response.headers[
        "Access-Control-Allow-Origin"
    ] = "*"

    response.headers[
        "Access-Control-Allow-Headers"
    ] = "*"

    response.headers[
        "Access-Control-Allow-Methods"
    ] = "GET, POST, OPTIONS"

    return response


# --------------------------------------------------
# MESSAGE PROCESSING
# --------------------------------------------------

def process_message(text):

    result = agent.process(
        text
    )

    reply = result.get(
        "reply"
    )

    if reply:

        conversation.add_user(
            text
        )

        conversation.add_assistant(
            reply
        )

    return result


# --------------------------------------------------
# RESPONSE
# --------------------------------------------------

def make_response(result):

    return jsonify({
        "ok": True,

        "reply": result.get(
            "reply"
        ),

        "response": result.get(
            "reply"
        ),

        "text": result.get(
            "reply"
        ),

        "type": result.get(
            "type",
            "ai"
        ),

        "tools": result.get(
            "tools",
            []
        ),

        "state": pc_tasks.get_state(),
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

            data = json.loads(
                raw
            )

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
        ),
        "agent": True,
    })


# --------------------------------------------------
# STATE
# --------------------------------------------------

@app.get("/state")
def state():

    return jsonify({
        "ok": True,
        "state": pc_tasks.get_state(),
    })


# --------------------------------------------------
# MEMORY
# --------------------------------------------------

@app.get("/memory")
def memory():

    return jsonify({
        "ok": True,
        "memory": conversation.get_recent(
            10
        ),
    })


# --------------------------------------------------
# TIMERS & REMINDERS
# --------------------------------------------------

def _timer_user_id():

    import os

    user_id = os.getenv(
        "SUPABASE_USER_ID"
    )

    if not user_id:

        raise RuntimeError(
            "SUPABASE_USER_ID is missing "
            "from .env"
        )

    return user_id


@app.get("/timers")
def timers():

    try:

        items = timer_manager.list_active(
            _timer_user_id()
        )

        return jsonify({
            "ok": True,
            "timers": items,
        })

    except Exception as e:

        print(
            "[TIMERS GET ERROR]",
            repr(e),
        )

        return jsonify({
            "ok": False,
            "error": str(e),
        }), 500


@app.get("/timers/due")
def timers_due():

    try:

        user_id = _timer_user_id()

        triggered = (
            timer_manager.claim_due(
                user_id
            )
        )

        recent = (
            timer_manager.recent_triggered(
                user_id,
                seconds=120,
            )
        )

        seen = set()
        due_items = []

        for item in triggered + recent:

            item_id = item.get(
                "id"
            )

            if item_id in seen:
                continue

            seen.add(
                item_id
            )

            due_items.append(
                item
            )

        return jsonify({
            "ok": True,
            "due": due_items,
        })

    except Exception as e:

        print(
            "[TIMERS DUE ERROR]",
            repr(e),
        )

        return jsonify({
            "ok": False,
            "error": str(e),
        }), 500


@app.delete("/timers/<int:item_id>")
def delete_timer(item_id):

    try:

        item = timer_manager.cancel(
            _timer_user_id(),
            item_id,
        )

        if not item:

            return jsonify({
                "ok": False,
                "error": (
                    "Timer or reminder "
                    "not found."
                ),
            }), 404

        return jsonify({
            "ok": True,
            "item": item,
        })

    except Exception as e:

        print(
            "[TIMERS DELETE ERROR]",
            repr(e),
        )

        return jsonify({
            "ok": False,
            "error": str(e),
        }), 500


# --------------------------------------------------
# RESET
# --------------------------------------------------

@app.post("/reset")
def reset():

    conversation.clear()

    return jsonify({
        "ok": True,
        "reply": (
            "Conversation reset, Sir."
        ),
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
            ),
        }), 400

    print(
        f"[JARVIS] Message: {text}"
    )

    try:

        result = process_message(
            text
        )

        print(
            "[JARVIS] Response type: "
            f"{result.get('type')}"
        )

        return make_response(
            result
        )

    except Exception as e:

        print(
            "[CHAT ERROR]",
            repr(e),
        )

        return jsonify({
            "ok": False,
            "reply": (
                f"I encountered an error, Sir: {e}"
            ),
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
            ),
        }), 400

    print(
        f"[JARVIS] Message: {text}"
    )

    try:

        result = process_message(
            text
        )

        print(
            "[JARVIS] Response type: "
            f"{result.get('type')}"
        )

        return make_response(
            result
        )

    except Exception as e:

        print(
            "[STREAM ERROR]",
            repr(e),
        )

        return jsonify({
            "ok": False,
            "reply": (
                f"I encountered an error, Sir: {e}"
            ),
        }), 500


# --------------------------------------------------
# OPTIONS / CORS
# --------------------------------------------------

@app.route(
    "/stream",
    methods=["OPTIONS"],
)
def stream_options():

    return "", 204


@app.route(
    "/chat",
    methods=["OPTIONS"],
)
def chat_options():

    return "", 204


@app.route(
    "/reset",
    methods=["OPTIONS"],
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
        "error": "Endpoint not found",
    }), 404


@app.errorhandler(500)
def internal_error(error):

    print(
        "[FLASK 500]",
        repr(error),
    )

    return jsonify({
        "ok": False,
        "error": str(error),
    }), 500


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":

    print()
    print("=" * 55)
    print("J.A.R.V.I.S. — AI AGENT")
    print("=" * 55)

    print(
        f"Server : http://{HOST}:{PORT}"
    )

    print(
        f"Model  : {MODEL}"
    )

    if OPENAI_API_KEY:
        print(
            "OpenAI : configured"
        )
    else:
        print(
            "OpenAI : MISSING API KEY"
        )

    print(
        "Agent  : tool calling enabled"
    )

    print("=" * 55)
    print()

    app.run(
        host=HOST,
        port=PORT,
        debug=settings.DEBUG,
        threaded=True,
    )