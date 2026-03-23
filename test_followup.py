import os
import sys

sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def test_followup():
    ctx = create_context()
    with open("test_out.txt", "w", encoding="utf-8") as f:
        f.write("--- Turn 1: Track order ---\n")
        reply1 = get_bot_response("track order 1234", ctx)
        f.write("Bot:\n" + reply1 + "\n")
        
        f.write("\n--- Turn 2: Yes ---\n")
        reply2 = get_bot_response("yes", ctx)
        f.write("Bot:\n" + reply2 + "\n")

        f.write("\n--- Turn 3: Check billing for 5678 ---\n")
        reply3 = get_bot_response("check billing for 5678", ctx)
        f.write("Bot:\n" + reply3 + "\n")

        f.write("\n--- Turn 4: Nah ---\n")
        reply4 = get_bot_response("nah", ctx)
        f.write("Bot:\n" + reply4 + "\n")

        # Test ambiguous during closure
        ctx2 = create_context()
        f.write("\n--- Test ambiguous closure ---\n")
        reply_track = get_bot_response("Cancel order 1234", ctx2)
        f.write("Bot (After Cancel):\n" + reply_track + "\n")
        
        f.write("\n--- User: asdasd ---\n")
        reply_ambig = get_bot_response("asdasd", ctx2)
        f.write("Bot:\n" + reply_ambig + "\n")
        
        f.write("\n--- User: no ---\n")
        reply_no = get_bot_response("no", ctx2)
        f.write("Bot:\n" + reply_no + "\n")

if __name__ == "__main__":
    test_followup()
