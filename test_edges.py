import os
import sys

sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def test_edges():
    ctx = create_context()
    with open("test_out.txt", "w", encoding="utf-8") as f:
        # Knowledge checks
        f.write("--- KB: Delivery Time ---\n")
        reply1 = get_bot_response("what is the delivery time?", ctx)
        f.write("Bot:\n" + reply1 + "\n")
        
        f.write("\n--- KB: Refund ---\n")
        reply2 = get_bot_response("what is your refund policy?", ctx)
        f.write("Bot:\n" + reply2 + "\n")

        # Edge Cases
        ctx2 = create_context()
        f.write("\n--- Edge: Partial Input ---\n")
        get_bot_response("track order", ctx2)
        reply3 = get_bot_response("12", ctx2)
        f.write("Bot:\n" + reply3 + "\n")

        f.write("\n--- Edge: Invalid DB ID ---\n")
        reply4 = get_bot_response("111", ctx2)
        f.write("Bot:\n" + reply4 + "\n")

        # Track Cancelled
        ctx3 = create_context()
        f.write("\n--- Edge: Already Cancelled ---\n")
        reply5 = get_bot_response("track order 4321", ctx3)
        f.write("Bot:\n" + reply5 + "\n")

        f.write("\n--- Edge: Missing Ambiguous Output ---\n")
        ctx4 = create_context()
        reply6 = get_bot_response("jibberishqwqweiwqe", ctx4)
        f.write("Bot:\n" + reply6 + "\n")

if __name__ == "__main__":
    test_edges()
