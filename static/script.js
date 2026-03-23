// Session ID persists across the conversation
let sessionId = null;
let lastSender = null; // Track consecutive messages

const chatMessages = document.getElementById("chatMessages");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");

// Send on Enter key
userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function getTimeString() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true });
}

function addMessage(text, sender, options = []) {
    const showTail = lastSender !== sender;
    lastSender = sender;

    const div = document.createElement("div");
    div.className = `message ${sender}-message`;
    if (!showTail) div.classList.add("no-tail");

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    const msgText = document.createElement("span");
    msgText.textContent = text;

    const time = document.createElement("span");
    time.className = "msg-time";
    time.textContent = getTimeString();

    bubble.appendChild(msgText);
    bubble.appendChild(time);
    div.appendChild(bubble);

    if (options && options.length > 0) {
        const optionsDiv = document.createElement("div");
        optionsDiv.className = "quick-replies";
        options.forEach(opt => {
            const btn = document.createElement("button");
            btn.className = "quick-reply-btn";
            btn.textContent = opt;
            btn.onclick = () => {
                userInput.value = opt;
                sendMessage();
            };
            optionsDiv.appendChild(btn);
        });
        div.appendChild(optionsDiv);
    }

    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTyping() {
    lastSender = null; // Reset so next bot message gets tail

    const div = document.createElement("div");
    div.className = "message bot-message";
    div.id = "typingIndicator";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble typing-indicator";
    bubble.innerHTML = "<span></span><span></span><span></span>";

    div.appendChild(bubble);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTyping() {
    const el = document.getElementById("typingIndicator");
    if (el) el.remove();
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    // Clear any active UI quick replies
    document.querySelectorAll(".quick-replies").forEach(el => el.remove());

    // Add user message
    addMessage(text, "user");
    userInput.value = "";
    sendBtn.disabled = true;

    // Show typing indicator
    showTyping();

    try {
        const body = { message: text };
        if (sessionId) body.session_id = sessionId;

        const startTime = Date.now();

        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        const data = await res.json();

        // Calculate dynamic typing delay based on message length
        const fetchTime = Date.now() - startTime;
        let typingDelay = 500;
        if (data.response) {
            // Approx 25ms per character, capped between 800ms and 3000ms
            const charDelay = Math.min(Math.max(data.response.length * 25, 800), 3000);
            typingDelay = Math.max(charDelay - fetchTime, 400); // subtract fetch time
        }

        await new Promise(r => setTimeout(r, typingDelay));

        // Store session ID for multi-turn conversations
        if (data.session_id) sessionId = data.session_id;

        removeTyping();

        if (data.response) {
            addMessage(data.response, "bot", data.options || []);
        } else if (data.error) {
            addMessage("Error: " + data.error, "bot");
        }
    } catch (err) {
        removeTyping();
        addMessage("Could not connect to server. Is it running?", "bot");
    }

    sendBtn.disabled = false;
    userInput.focus();
}

// Initialize chat on load
window.addEventListener('DOMContentLoaded', () => {
    showTyping();
    const startTime = Date.now();

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "/start" }),
    })
    .then(res => res.json())
    .then(async data => {
        const fetchTime = Date.now() - startTime;
        let typingDelay = 600;
        if (data.response) {
            const charDelay = Math.min(Math.max(data.response.length * 25, 800), 2000);
            typingDelay = Math.max(charDelay - fetchTime, 400);
        }
        await new Promise(r => setTimeout(r, typingDelay));

        if (data.session_id) sessionId = data.session_id;
        removeTyping();
        if (data.response) {
            addMessage(data.response, "bot", data.options || []);
        }
    })
    .catch(err => {
        removeTyping();
        addMessage("Could not connect to server.", "bot");
    });
});
