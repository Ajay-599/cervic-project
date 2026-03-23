import os
import sys

sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def test_msg(msg):
    print(f"\n--- Testing: '{msg}' ---")
    contexts = [create_context() for _ in range(3)]
    for i, ctx in enumerate(contexts):
        reply = get_bot_response(msg, ctx)
        # Just print the first line to see the variation
        print(f"Run {i+1}: {reply.splitlines()[0]}")

if __name__ == "__main__":
    test_msg("hello")
    test_msg("how are you")
    test_msg("what can you do")
    test_msg("who are you")
    test_msg("what is the meaning of life")
