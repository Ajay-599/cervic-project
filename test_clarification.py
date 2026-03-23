import os
import sys

sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def test_clarification():
    with open("test_out.txt", "w", encoding="utf-8") as f:
        ctx = create_context()
        f.write("--- Test 1: Number reply ---\n")
        reply1 = get_bot_response("order update", ctx)
        f.write("Bot:\n" + reply1 + "\n")
        
        reply2 = get_bot_response("1", ctx)
        f.write("Bot:\n" + reply2.splitlines()[0] + "\n")
        f.write("Clarification State after success 1: " + str(ctx.get("clarification_state")) + "\n")

        ctx = create_context()
        f.write("\n--- Test 2: Text reply ---\n")
        reply3 = get_bot_response("check order", ctx)
        f.write("Bot:\n" + reply3 + "\n")
        
        reply4 = get_bot_response("cancel order", ctx)
        f.write("Bot:\n" + reply4.splitlines()[0] + "\n")
        f.write("Clarification State after success 2: " + str(ctx.get("clarification_state")) + "\n")

if __name__ == "__main__":
    test_clarification()
