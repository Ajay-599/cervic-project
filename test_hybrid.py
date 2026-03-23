import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def print_convo(title, dialogue):
    print(f"\n{'='*50}")
    print(f"SCENARIO: {title}")
    print(f"{'='*50}")
    ctx = create_context()
    for user_msg in dialogue:
        print(f"\nUser: {user_msg}")
        bot_response = get_bot_response(user_msg, ctx)
        print(f"Bot:\n{bot_response}")
    return ctx

def run_hybrid_tests():
    # 1. Track Order (from training_data: "where is my order")
    print_convo("1. Tracking Flow", [
        "where is my order",
        "123",
    ])
    
    # 2. Cancel Order (from training_data: "cancel purchase")
    print_convo("2. Cancellation Flow", [
        "cancel purchase",
        "999",
    ])
    
    # 3. Ordering Flow (from training_data: "shopping" + explicit context testing)
    print_convo("3. Ordering Flow", [
        "shopping",
        "p2",
        "3",
        "yes"
    ])
    
    # 4. Small Talk (from training_data: "you are awesome")
    print_convo("4. Small Talk Flow", [
        "you are awesome",
        "who are you"
    ])
    
    # 5. Unknown Input (Fallback)
    # The new training_data fallback response should trigger.
    print_convo("5. Unknown Input (Fallback)", [
        "asdfghjkl",
        "I need help with a completely unrelated topic about flying cars"
    ])

if __name__ == "__main__":
    run_hybrid_tests()
