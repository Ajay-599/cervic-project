import sys
sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context
import copy

def test_quantity_extraction():
    # 1. Just a number
    ctx1 = create_context()
    get_bot_response("I want to buy", ctx1)
    get_bot_response("headphones", ctx1)
    reply1 = get_bot_response("2", ctx1)
    print("User: 2")
    assert ctx1["quantity"] == "2"

    # 2. Number in text
    ctx2 = create_context()
    get_bot_response("I want to buy", ctx2)
    get_bot_response("headphones", ctx2)
    reply2 = get_bot_response("buy 3", ctx2)
    print("User: buy 3")
    assert ctx2["quantity"] == "3"

    # 3. Text number
    ctx3 = create_context()
    get_bot_response("I want to buy", ctx3)
    get_bot_response("headphones", ctx3)
    reply3 = get_bot_response("I need four of them", ctx3)
    print("User: I need four of them")
    assert ctx3["quantity"] == "4"

    print("All quantity extraction tests passed!")

if __name__ == "__main__":
    test_quantity_extraction()
