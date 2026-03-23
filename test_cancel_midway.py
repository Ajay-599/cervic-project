import sys
sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context, State

def test_cancel_midway():
    ctx = create_context()
    
    # 1. Trigger intent
    reply1 = get_bot_response("I want to buy", ctx)
    print("User: I want to buy")
    print("Bot:\n", reply1, "\n")
    assert ctx["state"] == State.SLOT_FILLING

    # 2. Say cancel
    reply2 = get_bot_response("cancel that", ctx)
    print("User: cancel that")
    print("Bot:\n", reply2, "\n")
    
    # Check that it cancelled
    assert ctx["intent"] is None
    assert ctx["state"] == State.CLOSURE
    assert "cancel" in reply2.lower()

    print("Cancel midway test passed!")

if __name__ == "__main__":
    test_cancel_midway()
