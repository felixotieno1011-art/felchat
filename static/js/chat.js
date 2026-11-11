const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const chatMessages = document.getElementById('chat-messages');

let conversationHistory = [];
let isGenerating = false; // Prevents double-sending

function appendMessage(text, role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (role === 'assistant') {
        div.innerHTML = DOMPurify.sanitize(marked.parse(text));
        conversationHistory.push({ role: "assistant", content: text });
    } else {
        div.textContent = text;
        conversationHistory.push({ role: "user", content: text });
    }
    chatMessages.appendChild(div);
    // Smooth scroll to bottom
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isGenerating) return;

    isGenerating = true;
    btnSend.disabled = true; // Disable button while thinking

    appendMessage(text, 'user');
    chatInput.value = '';

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.textContent = 'FelChat is thinking...';
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });

    try {
        const historyToSend = conversationHistory.slice(-10, -1); 

        const res = await fetch('/chat/message', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: historyToSend })
        });

        let data;
        try {
            data = await res.json();
        } catch (e) {
            throw new Error("Server returned an invalid response (not JSON).");
        }

        chatMessages.removeChild(loadingDiv);

        if (!res.ok) {
            appendMessage(`Error: ${data.detail || 'Failed to get response'}`, 'assistant');
            return;
        }

        appendMessage(data.reply, 'assistant');

    } catch (err) {
        if (chatMessages.contains(loadingDiv)) {
            chatMessages.removeChild(loadingDiv);
        }
        appendMessage(`Network error: ${err.message}`, 'assistant');
    } finally {
        isGenerating = false;
        btnSend.disabled = false;
        chatInput.focus();
    }
}

// Use 'keydown' instead of deprecated 'keypress' to support mobile keyboards properly
btnSend.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
