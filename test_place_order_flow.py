import sys
sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context, State

def test_place_order_flow():
    ctx = create_context()
    
    # 1. User says "I want to buy something" -> place_order intent -> ask product
    reply1 = get_bot_response("I want to buy", ctx)
    print("User: I want to buy")
    print("Bot:\n", reply1, "\n")
    assert ctx["state"] == State.SLOT_FILLING
    assert ctx["slot_fill_state"]["product_id"] == "asking"
    
    # 2. User selects product "phone" -> asks quantity
    reply2 = get_bot_response("phone", ctx)
    print("User: phone")
    print("Bot:\n", reply2, "\n")
    assert ctx["entity_map"]["product_id"] == "p3"
    assert ctx["slot_fill_state"]["quantity"] == "asking"

    # 3. User selects quantity "two" -> asks confirmation
    reply3 = get_bot_response("two", ctx)
    print("User: two")
    print("Bot:\n", reply3, "\n")
    assert ctx["entity_map"]["quantity"] == "2"
    assert ctx["slot_fill_state"]["order_confirmed"] == "asking"
    assert "₹59998" in reply3  # 2 x 29999

    # 4. User confirms "yes" -> moves to resolution, returns order ID
    reply4 = get_bot_response("yes", ctx)
    print("User: yes")
    print("Bot:\n", reply4, "\n")
    assert ctx["entity_map"]["order_confirmed"] == "yes"
    assert "Your order ID is" in reply4
    
    print("All tests passed!")

if __name__ == "__main__":
    test_place_order_flow()
