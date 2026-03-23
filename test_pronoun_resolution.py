import sys
sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def test_pronoun_resolution():
    ctx = create_context()
    
    # User was talking about laptop recently (manually setting context as if from small talk)
    ctx["product_id"] = "p2" 
    
    # 1. "I want to buy it"
    ctx1 = dict(ctx)
    ctx1["entity_map"] = dict(ctx["entity_map"])
    ctx1["slot_fill_state"] = dict(ctx["slot_fill_state"])
    ctx1["intent_stack"] = list(ctx["intent_stack"])
    
    reply1 = get_bot_response("I want to buy it", ctx1)
    print("User: I want to buy it")
    print("Bot:\n", reply1, "\n")
    # It should have mapped 'it' to 'p2', and immediately asked for quantity
    assert ctx1["entity_map"]["product_id"] == "p2"
    assert ctx1["slot_fill_state"]["quantity"] == "asking"

    # 2. "I want to buy 2 of that"
    ctx2 = dict(ctx)
    ctx2["entity_map"] = dict(ctx["entity_map"])
    ctx2["slot_fill_state"] = dict(ctx["slot_fill_state"])
    ctx2["intent_stack"] = list(ctx["intent_stack"])
    
    reply2 = get_bot_response("I want to buy 2 of that", ctx2)
    print("User: I want to buy 2 of that")
    print("Bot:\n", reply2, "\n")
    # It should have mapped 'that' to 'p2' and '2' to quantity, immediately asking for confirmation
    assert ctx2["entity_map"]["product_id"] == "p2"
    assert ctx2["entity_map"]["quantity"] == "2"
    assert ctx2["slot_fill_state"]["order_confirmed"] == "asking"

    print("All pronoun tests passed!")

if __name__ == "__main__":
    test_pronoun_resolution()
