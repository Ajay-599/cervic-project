import os
import sys

sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context, State

def test_sentiment():
    with open("test_out.txt", "w", encoding="utf-8") as f:
        # Test 1: High negative
        ctx = create_context()
        ctx["sentiment"] = -0.8
        f.write("--- Test 1: High Negative (<-0.4) ---\n")
        reply1 = get_bot_response("track order", ctx)
        f.write("Bot:\n" + reply1 + "\n")

        # Test 2: High positive
        ctx = create_context()
        ctx["sentiment"] = 1.0
        f.write("\n--- Test 2: High Positive (>0.5) ---\n")
        reply2 = get_bot_response("check billing", ctx)
        f.write("Bot:\n" + reply2 + "\n")
        
        # Test 3: Neutral
        ctx = create_context()
        ctx["sentiment"] = 0.0
        f.write("\n--- Test 3: Neutral (0.0) ---\n")
        reply3 = get_bot_response("cancel order", ctx)
        f.write("Bot:\n" + reply3 + "\n")

if __name__ == "__main__":
    test_sentiment()
