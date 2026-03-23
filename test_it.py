import os
import sys

sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def test_it():
    with open("test_out.txt", "w", encoding="utf-8") as f:
        ctx = create_context()
        f.write("--- User: track order 1234 ---\n")
        reply1 = get_bot_response("track order 1234", ctx)
        f.write("Bot:\n" + reply1 + "\n")
        f.write(f"Entities: {ctx['entity_map']}\n")
        
        f.write("\n--- User: cancel it ---\n")
        reply2 = get_bot_response("cancel it", ctx)
        f.write("Bot:\n" + reply2 + "\n\n")

        ctx2 = create_context()
        f.write("--- User: check billing for 5678 ---\n")
        reply3 = get_bot_response("check billing for 5678", ctx2)
        f.write("Bot:\n" + reply3 + "\n")
        
        f.write("\n--- User: what is the status of that order? ---\n")
        reply4 = get_bot_response("what is the status of that order?", ctx2)
        f.write("Bot:\n" + reply4 + "\n")

if __name__ == "__main__":
    test_it()
