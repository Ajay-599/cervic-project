import os
import sys

sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def test_conv():
    ctx = create_context()
    with open("test_out.txt", "w", encoding="utf-8") as f:
        # 1. SLOT REQUEST
        f.write("--- SLOT REQUEST ---\n")
        reply1 = get_bot_response("track order", ctx)
        f.write("Bot:\n" + reply1 + "\n\n")
        
        # 2. VALIDATION ERROR
        f.write("--- VALIDATION ERROR ---\n")
        reply2 = get_bot_response("what", ctx)
        f.write("Bot:\n" + reply2 + "\n\n")

        # 3. CLOSURE ACKNOWLEDGEMENT
        ctx2 = create_context()
        get_bot_response("1234", ctx) # fake resolve
        f.write("--- CLOSURE ACK ---\n")
        reply3 = get_bot_response("yes", ctx)
        f.write("Bot:\n" + reply3 + "\n\n")

if __name__ == "__main__":
    test_conv()
