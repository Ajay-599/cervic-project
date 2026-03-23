import time
import random
import re
import uuid
from enum import Enum
from training_data import TRAINING_SCENARIOS, get_training_responses
from flask import Flask, request, jsonify, render_template

# Knowledge Base definition
KNOWLEDGE_BASE = {
    "delivery time": "Our standard delivery time is 5-7 business days depending on your location.",
    "refund policy": "Refunds are processed within 5-7 working days after cancellation or return.",
    "shipping details": "We ship via standard ground shipping. You will receive a tracking number once the order ships.",
    "contact": "You can reach our human support agents anytime by simply asking to 'speak to a human'.",
}

app = Flask(__name__)

# ============================================================
# Central Response Generator
# ============================================================

def generate_response(main: str, include_greeting: bool = False, include_transition: bool = False, follow_up: str = None) -> str:
    """
    Constructs a cohesive bot response blending a greeting (optional), the main payload, and a dynamic follow-up (optional).
    """
    parts = []
    
    if include_greeting:
        greetings = [
            "Hello! 👋",
            "Hi there! 😊",
            "Hey! ✨",
            "Greetings! 👋",
            "Hi! 😊",
            "Hello! Welcome to Cervic Support 👋",
            "Hi there! Thanks for reaching out to Cervic Support 👋"
        ]
        parts.append(random.choice(greetings))
    elif include_transition:
        transitions = ["Alright!", "Got it!", "Sure!", "No worries!", "Okay!", "Understood!"]
        main = f"{random.choice(transitions)} {main}"
        
    parts.append(main)
    
    if follow_up:
        parts.append(follow_up)
        
    return "\n\n".join(parts)


# ============================================================
# FSM State Definition
# ============================================================

class State(str, Enum):
    GREETING         = "GREETING"
    INTENT_DISCOVERY = "INTENT_DISCOVERY"
    SLOT_FILLING     = "SLOT_FILLING"
    RESOLUTION       = "RESOLUTION"
    CLOSURE          = "CLOSURE"
    ESCALATED        = "ESCALATED"


# Disambiguation menu text (used within INTENT_DISCOVERY state)
MENU_OPTIONS = [
    ("1", "track_order",   "Track order"),
    ("2", "cancel_order",  "Cancel order"),
    ("3", "check_billing", "Check billing"),
    ("4", "place_order",   "Place order"),
]

# ============================================================
# Session Storage & Analytics
# ============================================================

SESSION_TIMEOUT_SECONDS = 300  # 5 minutes

sessions = {}  # { session_id: context_dict }

# Global Analytics Data
analytics = {
    "total_messages": 0,
    "intents_detected": {},
    "fallbacks_triggered": 0,
    "escalations_triggered": 0
}

# Simulated order database
orders = {
    "1234": {"status": "Shipped",          "eta": "March 23, 2026", "email": "user1@email.com"},
    "5678": {"status": "Processing",       "eta": "March 25, 2026", "email": "user2@email.com"},
    "9999": {"status": "Delivered",        "eta": "March 20, 2026", "email": "user3@email.com"},
    "1111": {"status": "Out for Delivery", "eta": "Today",          "email": "user4@email.com"},
    "4321": {"status": "Cancelled",        "eta": "N/A",            "email": "user5@email.com"},
}

# Product Catalog
products = {
  "p1": {"name": "Headphones", "price": 1999},
  "p2": {"name": "Laptop", "price": 49999},
  "p3": {"name": "Phone", "price": 29999}
}

def get_product_listing() -> str:
    """Format the products dictionary into a readable catalog."""
    lines = []
    for pid, info in products.items():
        lines.append(f"• {info['name']}: {info['price']}")
    return "\n".join(lines)

def handle_knowledge_query(msg: str) -> str | None:
    msg_lower = msg.lower()
    for key, response in KNOWLEDGE_BASE.items():
        if key in msg_lower:
            return response
    # Loose matching backups
    if "delivery" in msg_lower or "arrive" in msg_lower:
        return KNOWLEDGE_BASE["delivery time"]
    if "refund" in msg_lower or "return" in msg_lower:
        return KNOWLEDGE_BASE["refund policy"]
    if "shipping" in msg_lower or "ship" in msg_lower:
        return KNOWLEDGE_BASE["shipping details"]
    return None

# Sentiment word weights (word → score from 0.0 to 1.0)
POSITIVE_WORDS = {
    "thanks": 0.3, "thank": 0.3, "great": 0.5, "good": 0.3,
    "awesome": 0.7, "love": 0.6, "excellent": 0.8, "perfect": 0.9,
    "nice": 0.3, "cool": 0.3, "happy": 0.5, "pleased": 0.5,
    "amazing": 0.7, "wonderful": 0.7, "fantastic": 0.8,
    "helpful": 0.5, "appreciate": 0.5, "glad": 0.4,
}
NEGATIVE_WORDS = {
    "bad": 0.4, "worst": 0.9, "terrible": 0.8, "hate": 0.7,
    "angry": 0.7, "frustrated": 0.7, "annoyed": 0.5, "horrible": 0.8,
    "awful": 0.8, "useless": 0.6, "stupid": 0.6, "slow": 0.3,
    "disappointing": 0.5, "disappointed": 0.5, "pathetic": 0.8,
    "trash": 0.7, "garbage": 0.7, "ridiculous": 0.6,
    "unacceptable": 0.7, "disgusting": 0.8, "furious": 0.9,
    "rubbish": 0.6, "sucks": 0.6, "broken": 0.4, "poor": 0.4,
}


# ============================================================
# Slot Registry — defines required slots per intent dynamically
# ============================================================

def _extract_order_id(message: str) -> str | None:
    """Extract a numeric order ID. Grabs any digits to handle partial input correctly."""
    match = re.search(r"\b(\d+)\b", message)
    return match.group(1) if match else None


def _extract_email(message: str) -> str | None:
    """Extract an email address from the message."""
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", message)
    return match.group(0) if match else None


def _validate_order_id(value: str) -> bool:
    """Validate that the order ID is a numeric string with 3+ digits."""
    return bool(value) and value.isdigit() and len(value) >= 3


def _validate_email(value: str) -> bool:
    """Basic email validation."""
    return bool(value) and "@" in value and "." in value


def _extract_product_id(message: str) -> str | None:
    message = message.lower()
    for pid, info in products.items():
        if pid.lower() in message or info["name"].lower() in message:
            return pid
    return None

def _validate_product_id(value: str) -> bool:
    return value in products

def ask_product_id(ctx: dict) -> str:
    return f"Here is our current product catalog:\n{get_product_listing()}\n\nPlease enter the product ID or name you wish to purchase. 🛒"

def _extract_quantity(message: str) -> str | None:
    match = re.search(r"\b(\d+)\b", message)
    if match: return match.group(1)
    words = message.lower().split()
    word_to_num = {"one": "1", "a": "1", "two": "2", "three": "3", "four": "4", "five": "5"}
    for w in words:
        if w in word_to_num: return word_to_num[w]
    return None

def _validate_quantity(value: str) -> bool:
    return bool(value) and value.isdigit() and int(value) > 0

def ask_quantity(ctx: dict) -> str:
    return "Great! How many would you like to order? 📦"

def _extract_order_confirmed(message: str) -> str | None:
    answer = message.lower().strip()
    yes_words = {"yes", "y", "yeah", "yep", "sure", "please", "confirm", "ok", "okay"}
    no_words  = {"no", "n", "nope", "nah", "cancel", "stop", "wait"}
    if any(re.search(rf"\b{w}\b", answer) for w in yes_words): return "yes"
    if any(re.search(rf"\b{w}\b", answer) for w in no_words): return "no"
    return None

def _validate_order_confirmed(value: str) -> bool:
    return value in ["yes", "no"]

def ask_confirmation(ctx: dict) -> str:
    pid = ctx["entity_map"].get("product_id")
    qty = ctx["entity_map"].get("quantity")
    if not pid or not qty: return "Could you please confirm your order? (yes/no)"
    name = products.get(pid, {}).get("name", "Unknown")
    price = products.get(pid, {}).get("price", 0)
    total = int(qty) * price
    return f"You are ordering {qty} {name} for ₹{total}. Confirm?"

# Each intent maps to a list of slot definitions:
#   name      — key in entity_map / slot_fill_state
#   extractor — function(message) -> value or None
#   validator — function(value) -> bool
#   prompt    — what to ask when the slot is missing
#   switch_prompt — what to say when switching intents
SLOT_REGISTRY = {
    "track_order": [
        {
            "name": "order_id",
            "extractor": _extract_order_id,
            "validator": _validate_order_id,
            "prompt": [
                "Could you share your order ID so I can track it for you? 😊",
                "I'll need your order number! 📦",
                "Absolutely ✨ Could you tell me your order ID?",
                "Not a problem at all! Please enter your order ID to continue. 👇",
                "I can certainly help with that. What is the order ID you want to track?"
            ],
            "switch_prompt": [
                "Got it! Switching to tracking. Could you provide your order ID? 😊",
                "Understood. Let's track your order instead! What is the order ID? 📦",
                "Sure, I can track that for you now ✨ Please share the order ID.",
                "Changing course to track an order. What's your order number?",
                "Okay, let's track a shipment! Could you give me the order ID?"
            ],
        },
    ],
    "cancel_order": [
        {
            "name": "order_id",
            "extractor": _extract_order_id,
            "validator": _validate_order_id,
            "prompt": [
                "I can certainly help you cancel your order. Could you share your order ID? 😊",
                "Let's get that cancelled for you. I'll need your order number! ❌",
                "Sure ✨ I can process a cancellation. Could you provide the order ID?",
                "I'd be happy to help you cancel. Please enter your order ID below. 👇",
                "To cancel your order, I'll just need your order ID first!"
            ],
            "switch_prompt": [
                "Got it, switching to cancellation. Could you provide your order ID? 😊",
                "Okay, let's cancel an order instead! What's your order ID? ❌",
                "Understood ✨ Switching to cancellation. Please share the order ID.",
                "No problem, I'll help you cancel that right away. What is the order number?",
                "Changing focus to cancel your order. Could you provide the order ID?"
            ],
        },
    ],
    "check_billing": [
        {
            "name": "order_id",
            "extractor": _extract_order_id,
            "validator": _validate_order_id,
            "prompt": [
                "I'd be happy to check the billing! Could you share your order ID? 💳",
                "To look up those billing details, I'll need your order number first 😊",
                "Sure ✨ I can pull up the billing info. What is your order ID?",
                "No problem at all! Could you share the order ID? 👇",
                "Let's look into your billing. Please enter your order ID."
            ],
            "switch_prompt": [
                "Got it! Switching to billing. Could you provide your order ID? 💳",
                "Okay, let's check your billing instead! What's the order ID? 😊",
                "Understood ✨ Switching to billing inquiries. Please share the order ID.",
                "No problem, let's look at your bill. Could you provide the order number?",
                "Changing course to check billing info. What is your order ID?"
            ],
        },
    ],
    "place_order": [
        {
            "name": "product_id",
            "extractor": _extract_product_id,
            "validator": _validate_product_id,
            "prompt": ask_product_id,
            "switch_prompt": ask_product_id,
        },
        {
            "name": "quantity",
            "extractor": _extract_quantity,
            "validator": _validate_quantity,
            "prompt": ask_quantity,
            "switch_prompt": ask_quantity,
        },
        {
            "name": "order_confirmed",
            "extractor": _extract_order_confirmed,
            "validator": _validate_order_confirmed,
            "prompt": ask_confirmation,
            "switch_prompt": ask_confirmation,
        }
    ],
}


# ============================================================
# Dynamic Slot Filling Helpers
# ============================================================

def init_slots_for_intent(ctx: dict, intent: str):
    """Initialize slot_fill_state and entity_map for the given intent from the registry."""
    # Track intent
    analytics["intents_detected"][intent] = analytics["intents_detected"].get(intent, 0) + 1

    slots = SLOT_REGISTRY.get(intent, [])
    ctx["slot_fill_state"] = {s["name"]: "missing" for s in slots}
    for s in slots:
        if s["name"] not in ctx["entity_map"]:
            ctx["entity_map"][s["name"]] = None


def try_fill_slots(ctx: dict, message: str):
    """Try to extract and validate all slots for the current intent from the message."""
    intent = ctx["intent"]
    slots = SLOT_REGISTRY.get(intent, [])

    for slot in slots:
        name = slot["name"]
        # Skip already filled slots
        if ctx["slot_fill_state"].get(name) == "filled":
            continue

        # Try to extract
        value = slot["extractor"](message)

        # Pronoun resolution: fallback to existing entity value if referred to by pronoun
        existing_val = ctx.get(name) or ctx["entity_map"].get(name)
        if not value and existing_val:
            pronouns = ["it", "that", "this", "that item", "this item", "the item", "that order", "this order", "the order", "that one", "this one"]
            msg_lower = message.lower()
            if any(re.search(rf"\b{p}\b", msg_lower) for p in pronouns):
                value = existing_val

        if value and slot["validator"](value):
            ctx["entity_map"][name] = value
            if name in ["product_id", "quantity", "order_confirmed"]:
                ctx[name] = value
            ctx["slot_fill_state"][name] = "filled"


def all_slots_filled(ctx: dict) -> bool:
    """Check if every required slot for the current intent is filled."""
    intent = ctx["intent"]
    slots = SLOT_REGISTRY.get(intent, [])
    return all(ctx["slot_fill_state"].get(s["name"]) == "filled" for s in slots)


def get_missing_slot_prompt(ctx: dict, use_switch: bool = False) -> str:
    """Return the prompt for the first unfilled slot. Uses switch_prompt if switching intents."""
    intent = ctx["intent"]
    slots = SLOT_REGISTRY.get(intent, [])

    for slot in slots:
        name = slot["name"]
        if ctx["slot_fill_state"].get(name) != "filled":
            ctx["slot_fill_state"][name] = "asking"
            prompt_list = slot["switch_prompt"] if use_switch else slot["prompt"]
            if callable(prompt_list):
                return prompt_list(ctx)
            if isinstance(prompt_list, list):
                return random.choice(prompt_list)
            return prompt_list

    return "Please provide the required information."


def get_validation_error(ctx: dict, last_input: str = "") -> str:
    """Return a user-friendly error for the first unfilled slot."""
    intent = ctx["intent"]
    slots = SLOT_REGISTRY.get(intent, [])

    for slot in slots:
        name = slot["name"]
        if ctx["slot_fill_state"].get(name) != "filled":
            ctx["slot_fill_state"][name] = "asking"
            
            if name == "product_id":
                return "I couldn't find that product. Please enter a valid product ID or name."
            if name == "quantity":
                return "I didn't catch a valid quantity. Please enter a number (e.g. 1)."
            if name == "order_confirmed":
                return "Please reply with 'yes' to confirm or 'no' to cancel."
            
            # Smart Partial Input Response
            if name == "order_id":
                match = re.search(r"\b(\d+)\b", last_input)
                if match:
                    val = match.group(1)
                    if len(val) < 3:
                        msg = [
                            f"You entered '{val}', but our order IDs are at least 3 digits. Please try again. 🤔",
                            f"I saw '{val}', but that seems a bit too short for a standard order ID! Could you double check? 👀",
                            f"Oops! '{val}' doesn't look like a complete order number. Can you try again? 😊"
                        ]
                        return random.choice(msg)
            
            clean_name = name.replace('_', ' ')
            fallback_msgs = [
                f"Hmm, I didn't quite catch a valid {clean_name}. Could you try typing that again? (e.g. 12345) 🤔",
                f"I'm sorry, I couldn't find a valid {clean_name} in your message. Could you share it once more? ✨",
                f"Oops! It looks like I missed your {clean_name}. Could you please provide it again? 😊",
                f"Could you double-check your {clean_name}? I didn't quite catch it! 👇"
            ]
            return random.choice(fallback_msgs)

    return "Something seems to be missing. Could you please try again? 😊"


# ============================================================
# Context Management
# ============================================================

def get_fallback_response(ctx: dict, msg: str = "") -> str:
    ctx["fallback_count"] = ctx.get("fallback_count", 0) + 1
    
    # If disambiguating, list the options
    if ctx.get("disambiguating") and ctx.get("options"):
        opts = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(ctx["options"])])
        return random.choice([
            "I'm not quite sure which one you meant. Do you want to:\n" + opts,
            "Could you clarify? Here are some options:\n" + opts,
            "Sorry, could you choose one of these?\n" + opts
        ])
        
    return random.choice(get_training_responses("fallback"))

def create_context() -> dict:
    """Create a fresh structured context object."""
    return {
        "intent": "",
        "intent_stack": [],
        "entity_map": {},
        "slot_fill_state": {},
        "conversation_topic": "",
        "sentiment": 0,
        "turn_count": 0,
        "confidence": 0.0,
        "pending_intent": None,
        "disambiguating": False,
        "retry_count": 0,
        "fallback_count": 0,
        "escalated": False,
        "state": State.GREETING,
        "last_accessed": time.time(),
        "last_summary": "",
        "product_id": None,
        "quantity": None,
        "order_confirmed": False,
    }


def get_or_create_session(session_id: str = None) -> tuple[str, dict]:
    """Get an existing session or create a new one."""
    now = time.time()
    if session_id and session_id in sessions:
        ctx = sessions[session_id]
        if now - ctx["last_accessed"] > SESSION_TIMEOUT_SECONDS:
            topic = ctx.get("conversation_topic") or "General"
            summary = f"Session timed out. Handled topic '{topic}' in {ctx.get('turn_count', 0)} turns. Final sentiment: {ctx.get('sentiment', 0)}."
            new_ctx = create_context()
            new_ctx["last_summary"] = summary
            sessions[session_id] = new_ctx
            print(f"  [TIMEOUT] Session {session_id} expired. Context reset.")
        else:
            ctx["last_accessed"] = now
        return session_id, sessions[session_id]

    new_id = session_id or str(uuid.uuid4())
    sessions[new_id] = create_context()
    return new_id, sessions[new_id]


def reset_context(ctx: dict):
    """Reset context after a task is completed, keeping sentiment and turn count."""
    sentiment = ctx["sentiment"]
    turn_count = ctx["turn_count"]
    ctx.update(create_context())
    ctx["sentiment"] = sentiment
    ctx["turn_count"] = turn_count


def update_sentiment(ctx: dict, message: str):
    """Adjust sentiment score based on weighted words. Scale: -1.0 to +1.0."""
    words = message.lower().split()
    pos_score = sum(POSITIVE_WORDS.get(w, 0.0) for w in words)
    neg_score = sum(NEGATIVE_WORDS.get(w, 0.0) for w in words)

    # Net delta for this message (-1 to +1 range)
    delta = max(-1.0, min(1.0, pos_score - neg_score))

    # Exponential moving average (new messages weigh 40%, history 60%)
    old = ctx["sentiment"]
    ctx["sentiment"] = round(max(-1.0, min(1.0, old * 0.6 + delta * 0.4)), 2)


def log_context(session_id: str, ctx: dict, user_msg: str, bot_msg: str):
    """Print context to server console for debugging."""
    print("\n" + "=" * 60)
    print(f"  SESSION: {session_id}")
    print(f"  USER:    {user_msg}")
    print(f"  BOT:     {bot_msg}")
    import json as _json
    print(f"  CONTEXT: {_json.dumps(ctx, indent=2)}")
    print("=" * 60 + "\n")


# ============================================================
# Escalation
# ============================================================

# Phrases that trigger immediate escalation to a human agent
ESCALATION_PHRASES = [
    "talk to human", "talk to agent", "talk to a human", "talk to a person",
    "human agent", "real agent", "real person", "live agent", "live person",
    "connect me to", "speak to human", "speak to agent",
    "need a human", "want a human", "want an agent",
    "agent",
]


def escalate_to_agent(session_id: str, ctx: dict, trigger: str) -> str:
    """
    Mark session as escalated, dump full context to server console,
    and return the escalation message to the user.

    trigger: 'explicit' | 'sentiment' | 'fallback'
    """
    ctx["escalated"] = True
    ctx["retry_count"] = 0
    ctx["disambiguating"] = False
    
    analytics["escalations_triggered"] += 1

    # --- Simulate sending context to human agent (printed to server console) ---
    print("\n" + "#" * 60)
    print("  🚨 ESCALATION TRIGGERED")
    print(f"  Trigger  : {trigger}")
    print(f"  Session  : {session_id}")
    print(f"  Sentiment: {ctx['sentiment']}")
    print(f"  Intent   : {ctx['intent']}")
    print(f"  Topic    : {ctx['conversation_topic']}")
    print(f"  Entities : {ctx['entity_map']}")
    print(f"  Slots    : {ctx['slot_fill_state']}")
    print(f"  Turns    : {ctx['turn_count']}")
    print(f"  Stack    : {ctx['intent_stack']}")
    print("  FULL CONTEXT:")
    import json as _json
    print(_json.dumps(ctx, indent=4, default=str))
    print("#" * 60 + "\n")

    trigger_note = {
        "explicit":  "You requested to speak with a human.",
        "sentiment": "We noticed you seem frustrated.",
        "fallback":  "We couldn\'t understand your request after multiple attempts.",
    }.get(trigger, "")

    return (
        f"🔴 Connecting you to a human agent...\n"
        f"{trigger_note}\n\n"
        "A support agent will be with you shortly. "
        "Your conversation context has been shared with them."
    )


# ============================================================
# Intent Detection
# ============================================================

def handle_small_talk(msg: str, ctx: dict) -> str:
    return random.choice(get_training_responses("small_talk"))


def detect_intent(message: str) -> dict:
    """
    Detect the user's intent with confidence scoring.
    Returns: { "intent": str, "confidence": float }

    Strong keywords  → confidence 0.95
    Weak keywords    → confidence 0.65
    No match         → small_talk at 1.0
    """
    message = message.lower().strip()

    best_intent = "small_talk"
    best_confidence = 0.0

    for scenario in TRAINING_SCENARIOS:
        intent_name = scenario["intent"]
        examples = sorted(scenario.get("examples", []), key=len, reverse=True)
        for phrase in examples:
            if phrase in message:
                # To maintain existing disambiguation behaviors without complex NLP,
                # we say exact matches or very long phrase matches are strong (0.95),
                # single word or short phrase matches are weak (0.65).
                words_in_phrase = len(phrase.split())
                is_exact = phrase == message
                
                # If exact match or a multi-word phrase is found inside user message, strong!
                if is_exact or words_in_phrase >= 2:
                    conf = 0.95
                else:
                    conf = 0.65
                
                if conf > best_confidence:
                    best_intent = intent_name
                    best_confidence = conf
                
                if best_confidence == 0.95:
                    break

    # If confidence wasn't conclusive, let's keep the legacy fallback for Knowledge Base check
    if best_confidence < 0.95:
        kb_resp = handle_knowledge_query(message)
        if kb_resp:
            return {"intent": "knowledge_query", "confidence": 0.95}

    # If nothing matched, return small_talk with full confidence
    if best_confidence == 0.0:
        return {"intent": "small_talk", "confidence": 1.0}

    return {"intent": best_intent, "confidence": round(best_confidence, 2)}


# ============================================================
# FSM State Handlers
# ============================================================

def _handle_greeting(msg: str, ctx: dict) -> str:
    """
    State: GREETING
    First turn only. Welcome the user, then move to INTENT_DISCOVERY.
    If first message already contains an intent, fast-track immediately.
    """
    result = detect_intent(msg)
    if result["confidence"] >= 0.75 and result["intent"] != "small_talk":
        # Fast-track: user included intent in greeting message
        ctx["state"] = State.INTENT_DISCOVERY
        return _handle_intent_discovery(msg, ctx)

    ctx["state"] = State.INTENT_DISCOVERY
    
    main_text = random.choice(get_training_responses("greeting"))
    
    follow_up_text = random.choice([
        "How can I assist you today?",
        "What do you need help with?",
        "What would you like to do?"
    ])
    
    ctx["options"] = ["Track Order", "Cancel Order", "Check Billing", "Place Order"]
    return generate_response(main=main_text, include_greeting=True, follow_up=follow_up_text)


def _handle_intent_discovery(msg: str, ctx: dict) -> str:
    """
    State: INTENT_DISCOVERY
    Ask user what they want to do. Parse intent.
    - Strong intent → start SLOT_FILLING
    - Medium intent → clarify (disambiguate)
    - Weak/None → small talk or Fallback
    """
    answer = msg.lower().strip()

    # --- Detect intent from message ---
    result = detect_intent(msg)
    intent     = result["intent"]
    confidence = result["confidence"]

    # --- Intercept Knowledge Base queries instantly ---
    if intent == "knowledge_query":
        kb_resp = handle_knowledge_query(msg)
        if kb_resp:
            return generate_response(main=kb_resp, include_transition=True, follow_up="Do you need help with anything else?")
        else:
            return generate_response(main="I couldn't find an exact answer for that. You can ask me about delivery times, refund policies, or shipping details.", include_transition=True, follow_up="Do you need help with anything else?")

    # --- Handle disambiguation menu selection ---
    if ctx["disambiguating"]:
        selected_intent = None
        # Numeric pick
        for num, intent_name, _ in MENU_OPTIONS:
            if answer == num:
                selected_intent = intent_name
                break
        # Text match fallback
        if not selected_intent:
            r = detect_intent(msg)
            if r["confidence"] >= 0.50 and r["intent"] != "small_talk":
                selected_intent = r["intent"]

        if selected_intent:
            ctx["disambiguating"] = False
            ctx["clarification_state"] = False
            ctx["retry_count"] = 0
            ctx["intent"] = selected_intent
            ctx["confidence"] = 0.85
            ctx["conversation_topic"] = selected_intent.replace("_", " ").title()
            ctx["state"] = State.SLOT_FILLING
            init_slots_for_intent(ctx, selected_intent)
            try_fill_slots(ctx, msg)
            if all_slots_filled(ctx):
                ctx["state"] = State.RESOLUTION
                return _handle_resolution(msg, ctx)
            return get_missing_slot_prompt(ctx)
        else:
            ctx["retry_count"] += 1
            if ctx["retry_count"] >= 2:
                return escalate_to_agent(_current_session_id, ctx, trigger="fallback")
            return get_fallback_response(ctx)

    # --- Detect intent from message ---
    result = detect_intent(msg)
    intent     = result["intent"]
    confidence = result["confidence"]
    ctx["confidence"] = confidence

    if confidence >= 0.75:
        ctx["retry_count"] = 0
        ctx["intent"] = intent
        ctx["conversation_topic"] = intent.replace("_", " ").title()

        if intent == "small_talk":
            ctx["conversation_topic"] = "Small Talk"
            ctx["state"] = State.INTENT_DISCOVERY
            return handle_small_talk(msg, ctx)

        ctx["state"] = State.SLOT_FILLING
        init_slots_for_intent(ctx, intent)
        try_fill_slots(ctx, msg)

        if all_slots_filled(ctx):
            ctx["state"] = State.RESOLUTION
            return _handle_resolution(msg, ctx)
        return get_missing_slot_prompt(ctx)

    elif confidence >= 0.50:
        ctx["disambiguating"] = True
        ctx["clarification_state"] = True
        ctx["options"] = ["Track Order", "Cancel Order", "Check Billing", "Place Order"]
        return (
            "Do you want to:\n"
            " 1. Track order\n"
            " 2. Cancel order\n"
            " 3. Check billing?\n"
            " 4. Place order?"
        )
    else:
        # Check if it was a small_talk query that fell through
        kb_resp = handle_knowledge_query(msg)
        if kb_resp:
            return generate_response(main=kb_resp, include_transition=True, follow_up="Do you need help with anything else?")
            
        analytics["fallbacks_triggered"] += 1
        ctx["retry_count"] += 1
        if ctx["retry_count"] >= 2:
            return escalate_to_agent(_current_session_id, ctx, trigger="fallback")
        ctx["disambiguating"] = True
        ctx["options"] = ["Track Order", "Cancel Order", "Check Billing", "Place Order"]
        return get_fallback_response(ctx, msg)


def _handle_slot_filling(msg: str, ctx: dict) -> str:
    """
    State: SLOT_FILLING
    Try to fill required slots from user message.
    - All slots filled → transition to RESOLUTION
    - Intent switch detected → push current intent, restart slot filling
    - Otherwise → ask for missing slot / validation error
    """
    msg_lower = msg.lower().strip()
    # Check if we are currently asking for a confirmation slot (in which case cancel/stop means "no")
    asking_confirm = any(
        ctx["slot_fill_state"].get(k) == "asking" for k in ["order_confirmed"]
    )
    import re
    if any(re.search(rf"\b{w}\b", msg_lower) for w in ["cancel", "nevermind", "stop", "abort", "quit"]) and not asking_confirm:
        ctx["intent"] = None
        ctx["intent_stack"] = []
        ctx["state"] = State.CLOSURE
        return random.choice([
            "No problem, I've cancelled that for you! Let me know if you need anything else. 😊",
            "Okay, process aborted. What else can I help you with today?",
            "Cancelled! I'm here if you need anything else."
        ])

    # Check for intent switch
    result = detect_intent(msg)
    new_intent     = result["intent"]
    new_confidence = result["confidence"]

    if new_intent != "small_talk" and new_intent != ctx["intent"] and new_confidence >= 0.50:
        if new_confidence >= 0.75:
            # Push current intent
            ctx["intent_stack"].append({
                "intent": ctx["intent"],
                "entity_map": dict(ctx["entity_map"]),
                "slot_fill_state": dict(ctx["slot_fill_state"]),
            })
            ctx["intent"]           = new_intent
            ctx["confidence"]       = new_confidence
            ctx["conversation_topic"] = new_intent.replace("_", " ").title()
            init_slots_for_intent(ctx, new_intent)
            try_fill_slots(ctx, msg)

            if all_slots_filled(ctx):
                ctx["state"] = State.RESOLUTION
                return _handle_resolution(msg, ctx)
            return get_missing_slot_prompt(ctx, use_switch=True)
        else:
            ctx["disambiguating"] = True
            ctx["state"] = State.INTENT_DISCOVERY
            variations = [
                "It sounds like you want something different. Are you trying to track or cancel an order?",
                "Did you change your mind? I can help you track, cancel, or check billing.",
                "I noticed you might be asking for something else. Do you want to look at a different order?",
                "Are we switching topics? Let me know if you need to track a package or cancel one.",
                "Let's refocus. Would you like me to track your order, cancel it, or check the bill?"
            ]
            return random.choice(variations)

    # Try filling slots for current intent
    try_fill_slots(ctx, msg)

    if all_slots_filled(ctx):
        ctx["state"] = State.RESOLUTION
        return _handle_resolution(msg, ctx)

    # Check if the next slot is missing (never asked) or asking (failed validation)
    intent = ctx["intent"]
    slots = SLOT_REGISTRY.get(intent, [])
    for slot in slots:
        name = slot["name"]
        if ctx["slot_fill_state"].get(name) == "missing":
            return get_missing_slot_prompt(ctx)
        if ctx["slot_fill_state"].get(name) == "asking":
            return get_validation_error(ctx, msg)

    return get_validation_error(ctx, msg)


def _handle_resolution(msg: str, ctx: dict) -> str:
    """
    State: RESOLUTION
    All slots are filled. Look up data, return result.
    If there's a stacked intent, pop and resume (back to SLOT_FILLING).
    Otherwise transition to CLOSURE.
    """
    order_id = ctx["entity_map"].get("order_id", "")
    intent   = ctx["intent"]

    response = _resolve_intent(intent, order_id, ctx)

    # POP intent stack if anything was pushed
    if ctx["intent_stack"]:
        prev = ctx["intent_stack"].pop()
        ctx["intent"]             = prev["intent"]
        ctx["entity_map"]         = prev["entity_map"]
        ctx["slot_fill_state"]    = prev["slot_fill_state"]
        ctx["conversation_topic"] = prev["intent"].replace("_", " ").title()

        prev_slots      = SLOT_REGISTRY.get(prev["intent"], [])
        prev_all_filled = all(prev["slot_fill_state"].get(s["name"]) == "filled" for s in prev_slots)

        if prev_all_filled and prev["entity_map"].get("order_id"):
            pop_response = _resolve_intent(prev["intent"], prev["entity_map"]["order_id"])
            response += f"\n\n🔁 Also resolving your previous request:\n{pop_response}"
            ctx["state"] = State.CLOSURE
            _begin_closure(ctx)
            return generate_response(main=response, include_transition=True, follow_up="Do you need help with anything else?")
        else:
            ctx["state"] = State.SLOT_FILLING
            missing_prompt = get_missing_slot_prompt(ctx)
            resume_texts = [
                f"\n\n🔁 Let's get back to your previous request! {missing_prompt}",
                f"\n\n🔁 Resuming your earlier inquiry: {missing_prompt}",
                f"\n\n🔁 Back to what we were doing! 😊 {missing_prompt}",
            ]
            response += random.choice(resume_texts)
            return generate_response(main=response)
    else:
        ctx["state"] = State.CLOSURE
        _begin_closure(ctx)
        return generate_response(main=response, include_transition=True, follow_up="Do you need help with anything else?")


def _begin_closure(ctx: dict):
    """Reset slots/intent but keep sentiment, turn_count, and entity_map for the CLOSURE state."""
    sentiment  = ctx["sentiment"]
    turn_count = ctx["turn_count"]
    entity_map = dict(ctx["entity_map"])

    ctx.update(create_context())

    ctx["sentiment"]  = sentiment
    ctx["turn_count"] = turn_count
    ctx["entity_map"] = entity_map
    ctx["state"]      = State.CLOSURE


def _handle_closure(msg: str, ctx: dict) -> str:
    """
    State: CLOSURE
    Ask if user needs anything else.
    - Yes-like → back to INTENT_DISCOVERY
    - No-like  → farewell, reset to GREETING
    """
    answer = msg.lower().strip()
    yes_words = {"yes", "y", "yeah", "yep", "sure", "please", "more", "another", "help"}
    no_words  = {"no", "n", "nope", "nah", "bye", "goodbye", "done", "thanks", "thank"}

    if any(re.search(rf"\b{w}\b", answer) for w in yes_words):
        ctx["state"] = State.INTENT_DISCOVERY
        ctx["options"] = ["Track Order", "Cancel Order", "Check Billing", "Place Order"]
        acks = ["Great! 😊", "Awesome! ✨", "Perfect! 👍", "Got it! ✅"]
        return generate_response(main=random.choice(acks), follow_up="How else can I help you today?")

    if any(re.search(rf"\b{w}\b", answer) for w in no_words):
        topic = ctx.get("conversation_topic") or "General"
        summary = f"Session closed. Handled topic '{topic}' in {ctx.get('turn_count', 0)} turns. Final sentiment: {ctx.get('sentiment', 0)}."
        ctx.update(create_context())
        ctx["last_summary"] = summary
        ctx["state"] = State.GREETING
        return generate_response(main="Thank you for contacting Cervic Support! Have a great day 😊")

    # Ambiguous — check if they started a new intent
    result = detect_intent(msg)
    if result["confidence"] >= 0.50 and result["intent"] != "small_talk":
        ctx["state"] = State.INTENT_DISCOVERY
        return _handle_intent_discovery(msg, ctx)

    # Still unclear
    ctx["state"] = State.CLOSURE
    ctx["options"] = ["Yes", "No"]
    return generate_response(main="Do you need help with anything else? (yes / no)")


def _handle_escalated(msg: str, ctx: dict) -> str:
    """
    State: ESCALATED
    Session is already escalated. Hold message until agent picks up.
    """
    return ("🔴 Your session is already with a human agent. "
            "Please wait for an agent to connect with you.")


# ============================================================
# FSM Dispatcher
# ============================================================

# Map each state to its handler
_FSM_HANDLERS = {
    State.GREETING:         _handle_greeting,
    State.INTENT_DISCOVERY: _handle_intent_discovery,
    State.SLOT_FILLING:     _handle_slot_filling,
    State.RESOLUTION:       _handle_resolution,
    State.CLOSURE:          _handle_closure,
    State.ESCALATED:        _handle_escalated,
}


def apply_sentiment_modifiers(response: str, ctx: dict) -> str:
    """Prepends a sentiment-based empathetic or positive prefix to the response."""
    if ctx.get("escalated") or ctx.get("state") == State.ESCALATED:
        return response

    sentiment = ctx["sentiment"]
    prefix = ""

    if sentiment < -0.4:
        apologies = [
            "I'm so sorry for the frustration. ",
            "I completely understand why you're upset. ",
            "I apologize for the difficulties you're facing. ",
            "I'm sorry things haven't been smooth. ",
            "Please accept my apologies for the hassle. "
        ]
        prefix = random.choice(apologies)
    elif sentiment > 0.5:
        positives = [
            "I'm glad I can help! ",
            "It's always great to hear from you! ",
            "Awesome, I'm happy to assist! ",
            "I appreciate that positive energy! ",
            "Wonderful! Let's keep things moving. "
        ]
        prefix = random.choice(positives)

    if prefix.strip() in response:
        return response

    return prefix + response


def get_bot_response(user_message: str, ctx: dict) -> str:
    """
    FSM Dispatcher — central entry point for every user message.

    1. Increment turn count, update sentiment
    2. Check for explicit escalation phrase (any state)
    3. Route to correct state handler
    4. Log state transition to console
    """
    if user_message.strip() and user_message != "/start":
        analytics["total_messages"] += 1
        
    ctx["turn_count"] += 1
    update_sentiment(ctx, user_message)
    answer = user_message.lower().strip()

    # /start hook for initial greeting from frontend
    if answer == "/start":
        ctx.update(create_context())
        return _handle_greeting(user_message, ctx)

    # Cross-state: explicit escalation check
    if not ctx["escalated"]:
        for phrase in ESCALATION_PHRASES:
            if phrase in answer:
                ctx["state"] = State.ESCALATED
                return escalate_to_agent(_current_session_id, ctx, trigger="explicit")

    prev_state = ctx["state"]
    handler    = _FSM_HANDLERS.get(ctx["state"], _handle_greeting)
    response   = handler(user_message, ctx)

    response = apply_sentiment_modifiers(response, ctx)

    # Log state transition
    print(f"  [FSM] {prev_state} -> {ctx['state']}  (turn {ctx['turn_count']})")

    return response


def _resolve_intent(intent: str, order_id: str, ctx: dict = None) -> str:
    """Execute the resolution logic for a given intent and order_id."""
    order = orders.get(order_id)

    if intent == "track_order":
        if order:
            if order["status"] == "Cancelled":
                return random.choice([
                    f"Order #{order_id} was cancelled. There is no active tracking information.",
                    f"It looks like order #{order_id} was cancelled, so it won't be delivered.",
                    f"We cannot track order #{order_id} because it has been cancelled."
                ])
            elif order["status"] == "Delivered":
                return random.choice([
                    f"Good news! Order #{order_id} was already delivered on {order['eta']}.",
                    f"Your order #{order_id} has arrived! It was delivered on {order['eta']}.",
                    f"Looking at order #{order_id}, it shows as Delivered!"
                ])
            responses = [
                f"📦 Order #{order_id}\nStatus: {order['status']}\nEstimated Delivery: {order['eta']}",
                f"Here are the details for your order 📦 #{order_id}:\nIt is currently '{order['status']}'. Expect it by: {order['eta']}.",
                f"I found your order 📦 #{order_id}! Its status is '{order['status']}' and estimated delivery is {order['eta']}.",
                f"Tracking info for order 📦 #{order_id}:\nCurrent Status: {order['status']}\nETA: {order['eta']}",
                f"Good news! Your order 📦 #{order_id} is '{order['status']}'. It should arrive by {order['eta']}."
            ]
            return random.choice(responses)
        
        not_found_responses = [
            f"❌ I checked everywhere, but order #{order_id} doesn't exist in our system. Could you verify the number?",
            f"❌ Are you sure #{order_id} is correct? I can't find tracking info for it.",
            f"❌ Order #{order_id} came up empty. Do you have another order number to track?",
            f"❌ We have no record of order #{order_id}. Please check the number and try again.",
            f"❌ Sorry, order #{order_id} is not in our system. Tracking is unavailable."
        ]
        return random.choice(not_found_responses)

    elif intent == "cancel_order":
        if order:
            if order["status"] == "Cancelled":
                already_responses = [
                    f"Order #{order_id} is already cancelled.",
                    f"It looks like order #{order_id} has already been cancelled.",
                    f"No need to worry, order #{order_id} was already cancelled.",
                    f"That order (#{order_id}) is currently showing as cancelled in our system.",
                    f"Order #{order_id} is already marked as cancelled."
                ]
                return random.choice(already_responses)
            elif order["status"] == "Delivered":
                deliv_responses = [
                    f"Order #{order_id} has already been delivered on {order['eta']}. Please contact support for returns.",
                    f"Since order #{order_id} is already delivered, you'll need to initiate a return with support.",
                    f"We cannot cancel order #{order_id} because it was already delivered. Try a return request.",
                    f"Order #{order_id} is delivered. Please reach out to support for a return.",
                    f"Too late to cancel! Order #{order_id} is already delivered. Contact support to return it."
                ]
                return random.choice(deliv_responses)
            else:
                order["status"] = "Cancelled"
                order["eta"] = "N/A"
                success_responses = [
                    f"✅ Order #{order_id} has been cancelled successfully. You will receive a refund within 5-7 days.",
                    f"✅ Got it! Order #{order_id} is now cancelled. Expect your refund in 5-7 days.",
                    f"✅ Your cancellation for order #{order_id} was successful. A refund will be issued in 5-7 working days.",
                    f"✅ Cancelled! Order #{order_id} is no longer active. Refunds take 5-7 days.",
                    f"✅ We've successfully cancelled order #{order_id}. You should see a refund in 5-7 days."
                ]
                return random.choice(success_responses)
        
        not_found_responses = [
            f"❌ I checked everywhere, but order #{order_id} doesn't exist. I cannot cancel it.",
            f"❌ I couldn't find an order matching #{order_id} to cancel. Are you sure that's the right ID?",
            f"❌ Hmm, order #{order_id} came up empty. Do you have another order number?",
            f"❌ We have no record of order #{order_id}. Please check the number and try again.",
            f"❌ Sorry, order #{order_id} is not in our system. Cancellation failed."
        ]
        return random.choice(not_found_responses)

    elif intent == "check_billing":
        if order:
            responses = [
                f"💳 Order #{order_id}\nBilling Status: {order.get('billing', 'Paid')}\nEmail: {order.get('email', 'N/A')}",
                f"Here is the billing info for order 💳 #{order_id}:\nStatus is {order.get('billing', 'Paid')}. Associated email: {order.get('email', 'N/A')}.",
                f"For order 💳 #{order_id}, the bill is {order.get('billing', 'Paid')}. The email on file is {order.get('email', 'N/A')}.",
                f"Billing Details 💳 (Order #{order_id}):\nStatus: {order.get('billing', 'Paid')}\nEmail Address: {order.get('email', 'N/A')}",
                f"I checked order 💳 #{order_id}. It is {order.get('billing', 'Paid')}, linked to {order.get('email', 'N/A')}."
            ]
            return random.choice(responses)
            
        not_found_responses = [
            f"❌ Order #{order_id} was not found. Cannot retrieve billing info.",
            f"❌ I couldn't locate order #{order_id} to check its billing. Please verify the ID.",
            f"❌ No billing info found because order #{order_id} doesn't exist in our system.",
            f"❌ We have no record of order #{order_id}. Please check the number and try again.",
            f"❌ Sorry, order #{order_id} is not in our system. Cannot fetch billing details."
        ]
        return random.choice(not_found_responses)

    elif intent == "place_order":
        pid = ctx["entity_map"].get("product_id") if ctx else None
        qty = ctx["entity_map"].get("quantity") if ctx else None
        conf = ctx["entity_map"].get("order_confirmed") if ctx else None

        if conf == "yes" and pid and qty:
            new_id = str(random.randint(1000, 9999))
            orders[new_id] = {
                "status": "Processing",
                "eta": "3 days"
            }
            success_messages = [
                f"Great choice! 😊 Your order ID is {new_id}.",
                f"Awesome, placing your order now! Your order ID is {new_id}.",
                f"Your order has been successfully placed 🎉 Your order ID is {new_id}."
            ]
            return random.choice(success_messages)
        else:
            return "❌ Okay, I have cancelled the order process. Let me know if you need anything else!"

    error_responses = [
        "Something went wrong.",
        "Oops, an unexpected error occurred.",
        "I'm sorry, I encountered an issue while processing your request.",
        "An error happened on my end. Could you try again?",
        "Something failed while looking that up. Please retry."
    ]
    return random.choice(error_responses)


def _resolve_and_pop(ctx: dict) -> str:
    """Resolve the current intent, then pop the previous intent from the stack and resume it."""
    order_id = ctx["entity_map"].get("order_id", "")
    intent = ctx["intent"]

    response = _resolve_intent(intent, order_id)

    # POP: check if there's a previous intent to resume
    if ctx["intent_stack"]:
        prev = ctx["intent_stack"].pop()
        ctx["intent"] = prev["intent"]
        ctx["entity_map"] = prev["entity_map"]
        ctx["slot_fill_state"] = prev["slot_fill_state"]
        ctx["conversation_topic"] = prev["intent"].replace("_", " ").title()

        resumed_label = prev["intent"].replace("_", " ")

        # Check if previous intent had all slots filled
        prev_slots = SLOT_REGISTRY.get(prev["intent"], [])
        prev_all_filled = all(prev["slot_fill_state"].get(s["name"]) == "filled" for s in prev_slots)

        if prev_all_filled and prev["entity_map"].get("order_id"):
            pop_response = _resolve_intent(prev["intent"], prev["entity_map"]["order_id"])
            response += f"\n\n🔁 Also resolving your previous request:\n{pop_response}"
            reset_context(ctx)
        else:
            # Find what slot is still missing
            missing_prompt = get_missing_slot_prompt(ctx)
            response += f"\n\n🔁 Resuming: {resumed_label}. {missing_prompt}"
    else:
        reset_context(ctx)

    return response


# ============================================================
# Flask Routes & Dashboard Analytics
# ============================================================

def log_analytics_dashboard():
    """Print an ASCII dashboard of current analytics."""
    print("\n" + "="*45)
    print("📊 ANALYTICS DASHBOARD".center(45))
    print("="*45)
    print(f"Total Messages : {analytics['total_messages']}")
    print(f"Fallbacks      : {analytics['fallbacks_triggered']}")
    print(f"Escalations    : {analytics['escalations_triggered']}")
    print("-" * 45)
    print("Intents Detected:")
    if not analytics["intents_detected"]:
        print("  (none)")
    else:
        for k, v in analytics["intents_detected"].items():
            print(f"  - {k:<15} : {v}")
    print("="*45 + "\n")

# Module-level holder so escalate_to_agent() can access the session ID
# set by the /chat route handler
_current_session_id: str = ""

@app.route("/chat", methods=["POST"])
def chat():
    """
    POST /chat
    Expects JSON: { "message": "...", "session_id": "..." (optional) }
    Returns JSON: { "response": "...", "session_id": "...", "context": {...} }
    """
    data = request.get_json()

    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field in request body"}), 400

    user_message = data["message"]

    if not isinstance(user_message, str) or not user_message.strip():
        return jsonify({"error": "'message' must be a non-empty string"}), 400

    # Apply mock delay to simulate elapsed time
    s_id = data.get("session_id")
    if s_id and s_id in sessions and "mock_delay_seconds" in data:
        sessions[s_id]["last_accessed"] -= data.get("mock_delay_seconds", 0)

    # Get or create session
    session_id, ctx = get_or_create_session(s_id)

    # Pass session_id into bot logic (needed for escalation logging)
    global _current_session_id
    _current_session_id = session_id

    bot_reply = get_bot_response(user_message, ctx)

    # --- TRIGGER 2: Sentiment-based escalation ---
    if ctx["sentiment"] < -0.4 and not ctx["escalated"]:
        bot_reply += ("\n\n⚠️ I can see you're frustrated. "
                      "Would you like me to connect you to a human agent? "
                      "Just say **'talk to human'** or **'agent'**.")
        ctx["options"] = ["Talk to human", "Continue chat"]

    # Pop options from context so they don't pollute the persistent state 
    # but still get delivered in the JSON payload
    options = ctx.pop("options", [])

    # Debug: print context to server console
    log_context(session_id, ctx, user_message, bot_reply)
    log_analytics_dashboard()

    return jsonify({
        "response": bot_reply,
        "options": options,
        "session_id": session_id,
        "context": dict(ctx),
    })


@app.route("/", methods=["GET"])
def index():
    """Serve the chat frontend."""
    return render_template("index.html")


@app.route("/analytics", methods=["GET"])
def get_analytics():
    """Returns the live chatbot analytics metrics as JSON."""
    return jsonify(analytics)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
