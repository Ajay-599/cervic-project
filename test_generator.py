import os
import sys

sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def test_gen():
    ctx = create_context()
    with open("test_out.txt", "w", encoding="utf-8") as f:
        # 1. GREETING
        f.write("--- GREETING ---\n")
        reply1 = get_bot_response("hi", ctx)
        f.write("Bot:\n" + reply1 + "\n\n")
        
        # 2. INTENT_DISCOVERY (Knowledge)
        f.write("--- KB INTERCEPT ---\n")
        reply2 = get_bot_response("what is the delivery time?", ctx)
        f.write("Bot:\n" + reply2 + "\n\n")

        # 3. SLOT_FILLING
        ctx2 = create_context()
        get_bot_response("/start", ctx2) # Jump to discovery
        f.write("--- MISSING PROMPT ---\n")
        reply3 = get_bot_response("track order", ctx2)
        f.write("Bot:\n" + reply3 + "\n\n")

        # 4. RESOLUTION
        f.write("--- RESOLUTION ---\n")
        reply4 = get_bot_response("1234", ctx2)
        f.write("Bot:\n" + reply4 + "\n\n")

        # 5. CLOSURE
        f.write("--- CLOSURE AMBIGUOUS ---\n")
        reply5 = get_bot_response("wait what", ctx2)
        f.write("Bot:\n" + reply5 + "\n\n")
        
        f.write("--- CLOSURE NO ---\n")
        reply6 = get_bot_response("no", ctx2)
        f.write("Bot:\n" + reply6 + "\n\n")

if __name__ == "__main__":
    test_gen()
