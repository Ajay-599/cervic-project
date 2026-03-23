import os
import sys

sys.path.insert(0, r"c:\Users\Ajay\Desktop\cervic")
from app import get_bot_response, create_context

def run_convo(title, convo):
    ctx = create_context()
    print(f"=== {title} ===")
    for msg in convo:
        print(f"USER: {msg}")
        reply = get_bot_response(msg, ctx)
        print(f"BOT: {reply}\n")
    print("-" * 50)

def main():
    convo1 = [
        "Hello!",
        "What's the delivery time?",
        "Okay, track my order",
        "1234",
        "no"
    ]
    
    convo2 = [
        "I am so angry right now this is terrible!",
        "cancel order 9999",
        "what about 4321",
        "fine cancel 5678",
        "no"
    ]
    
    convo3 = [
        "hey there",
        "I'm really happy with your service, amazing!",
        "check billing for order 1111",
        "no"
    ]
    
    convo4 = [
        "hello",
        "asdfsdfsd",
        "wait tracking",
        "12",
        "1234",
        "no"
    ]
    
    convo5 = [
        "how are you",
        "what can you do",
        "track order 1234",
        "cancel it",
        "no"
    ]

    with open("c_out.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        run_convo("Conversation 1: Happy Path & KB", convo1)
        run_convo("Conversation 2: Emotional (Angry) & Cancellations", convo2)
        run_convo("Conversation 3: Emotional (Happy) & Billing", convo3)
        run_convo("Conversation 4: Ambiguous Input & Validation", convo4)
        run_convo("Conversation 5: Small Talk & Context Memory", convo5)
        sys.stdout = sys.__stdout__

if __name__ == "__main__":
    main()
