import os, json

import re, shutil

# Stored OUTSIDE the project folder, so editors / Live Server that watch the
# project never see it change (that was what reloaded the page on every save).
MEMORY_DIR  = os.path.join(os.path.expanduser("~"), ".jarvis")
MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.json")
_OLD_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")

os.makedirs(MEMORY_DIR, exist_ok=True)
if os.path.exists(_OLD_FILE) and not os.path.exists(MEMORY_FILE):
    shutil.move(_OLD_FILE, MEMORY_FILE)   # keep your existing memories

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return []

def save_memory(mem):
    tmp = MEMORY_FILE + ".tmp"
    with open(tmp, 'w') as f:
        json.dump(mem, f, indent=2)
    os.replace(tmp, MEMORY_FILE)   # atomic: never leaves a half-written file

memory = load_memory()

def build_memory_block():
    if not memory:
        return ""
    lines = "\n".join(f"- {m}" for m in memory)
    return f"\n\nThings the user has told you to remember:\n{lines}\nUse these naturally when relevant."

_SAVE_RE   = re.compile(r"^(?:please\s+)?(?:remember(?:\s+that)?|note\s+that|save\s+that|store\s+that)[\s:,]+(.+)$", re.I)
_FORGET_RE = re.compile(r"^(?:please\s+)?forget(?:\s+that)?[\s:,]+(.+)$", re.I)

def handle_memory_command(msg):
    t = msg.lower().strip()

    # Save — only when the sentence STARTS with the trigger, and do it silently.
    m = _SAVE_RE.match(msg.strip())
    if m:
        fact = m.group(1).strip().rstrip('.')
        if fact and fact.lower() not in [x.lower() for x in memory]:
            memory.append(fact)
            save_memory(memory)
        return '__silent__Saved to memory'

    m = _FORGET_RE.match(msg.strip())
    if m:
        keyword = m.group(1).strip().lower()
        removed = [x for x in memory if keyword in x.lower()]
        if removed:
            for r in removed:
                memory.remove(r)
            save_memory(memory)
            return '__silent__Removed from memory'
        return '__raw__Nothing matching that in memory, Sir.'

    recall_phrases = ['what do you remember', 'list memory', 'show memory',
                      'recall everything', 'what is in your memory',
                      "what's in your memory", 'show me your memory']
    if any(p in t for p in recall_phrases):
        if not memory:
            return "__raw__Memory is empty, Sir."
        lines = "\n".join(f"{i+1}. {m}" for i, m in enumerate(memory))
        return f"__raw__Here's what I'm holding:\n{lines}"

    return None

def wipe_memory():
    memory.clear()
    save_memory(memory)