const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const chatMessages = document.getElementById('chat-messages');

function appendMessage(text, role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // 1. Show user message
    appendMessage(text, 'user');
    chatInput.value = '';

    // 2. Show loading state
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant';
    loadingDiv.textContent = 'FelChat is thinking...';
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // 3. Send to backend
    try {
        const token = localStorage.getItem('felchat_token');
        const res = await fetch('/chat/message', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ message: text })
        });

        const data = await res.json();
        chatMessages.removeChild(loadingDiv);

        if (!res.ok) {
            appendMessage(`Error: ${data.detail || 'Failed to get response'}`, 'assistant');
            return;
        }

        // 4. Show AI response
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
