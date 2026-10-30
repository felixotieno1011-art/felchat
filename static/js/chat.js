const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const chatMessages = document.getElementById('chat-messages');

// This array holds the conversation history
let conversationHistory = [];

function appendMessage(text, role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (role === 'assistant') {
        div.innerHTML = marked.parse(text);
        // Save to history
        conversationHistory.push({ role: "assistant", content: text });
    } else {
        div.textContent = text;
        // Save to history
        conversationHistory.push({ role: "user", content: text });
    }
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // Show user message (and add to history)
    appendMessage(text, 'user');
    chatInput.value = '';

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.textContent = 'FelChat is thinking...';
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const token = localStorage.getItem('felchat_token');
        
        // We send the history BEFORE the current message (the current message is handled by the backend)
        // We limit to the last 10 messages to save tokens
        const historyToSend = conversationHistory.slice(-10, -1); 

        const res = await fetch('/chat/message', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ 
                message: text,
                history: historyToSend
            })
        });

        const data = await res.json();
        chatMessages.removeChild(loadingDiv);

        if (!res.ok) {
            appendMessage(`Error: ${data.detail || 'Failed to get response'}`, 'assistant');
            return;
        }

        appendMessage(data.reply, 'assistant');

    } catch (err) {
        chatMessages.removeChild(loadingDiv);
        appendMessage(`Network error: ${err.message}`, 'assistant');
    }
}

btnSend.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
