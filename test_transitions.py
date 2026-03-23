import os
import sys

sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def test_transitions():
    with open("test_out.txt", "w", encoding="utf-8") as f:
        # 1. Knowledge Base hit (should have transition)
        ctx = create_context()
        f.write("--- KB INTERCEPT ---\n")
        reply1 = get_bot_response("what is the delivery time?", ctx)
        f.write("Bot:\n" + reply1 + "\n\n")

        # 2. RESOLUTION hit (should have transition)
        ctx2 = create_context()
        get_bot_response("track order", ctx2)
        f.write("--- RESOLUTION ---\n")
        reply2 = get_bot_response("1234", ctx2)
        f.write("Bot:\n" + reply2 + "\n\n")

if __name__ == "__main__":
    test_transitions()
