const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const chatMessages = document.getElementById('chat-messages');

let conversationHistory = [];
let isGenerating = false;

function appendMessage(text, role, saveToHistory = true) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = `avatar ${role}`;
    avatar.textContent = role === 'user' ? 'U' : 'F'; 
    
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (role === 'assistant') {
        div.innerHTML = DOMPurify.sanitize(marked.parse(text));
        
        div.querySelectorAll('pre').forEach(pre => {
            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.textContent = 'Copy';
            btn.onclick = () => {
                navigator.clipboard.writeText(pre.innerText);
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = 'Copy', 2000);
            };
            pre.appendChild(btn);
        });
        div.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
    } else {
        div.textContent = text;
    }
    
    row.appendChild(avatar);
    row.appendChild(div);
    chatMessages.appendChild(row);
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
    
    if (saveToHistory) conversationHistory.push({ role: role, content: text });
    
    return div; // Return the div so the streamer can update it
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isGenerating) return;

    isGenerating = true;
    btnSend.disabled = true;

    appendMessage(text, 'user');
    chatInput.value = '';

    // Typing Indicator setup
    const loadingRow = document.createElement('div');
    loadingRow.className = 'message-row assistant';
    loadingRow.innerHTML = `
        <div class="avatar assistant">F</div>
        <div class="message assistant">
            <div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>
        </div>`;
    chatMessages.appendChild(loadingRow);
    chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });

    try {
        const historyToSend = conversationHistory.slice(-10, -1); 

        const res = await fetch('/chat/message', {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: historyToSend })
        });

        if (res.status === 401) { window.handleSessionExpired(); return; }

        // Remove the typing indicator
        chatMessages.removeChild(loadingRow);

        if (!res.ok) {
            const data = await res.json();
            appendMessage(`Error: ${data.detail || 'Failed'}`, 'assistant', false);
            return;
        }

        // Create a new empty message bubble for the stream
        const messageDiv = appendMessage('', 'assistant', false);
        let fullText = '';

        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            fullText += chunk;
            
            // Render markdown live
            messageDiv.innerHTML = DOMPurify.sanitize(marked.parse(fullText));
            messageDiv.querySelectorAll('pre code').forEach((block) => hljs.highlightElement(block));
            chatMessages.scrollTo({ top: chatMessages.scrollHeight, behavior: 'smooth' });
        }

        // Save the final streamed message to history
        const isWAFBlock = fullText.includes("Security Alert");
        if (!isWAFBlock) conversationHistory.push({ role: 'assistant', content: fullText });

    } catch (err) {
        if (chatMessages.contains(loadingRow)) chatMessages.removeChild(loadingRow);
        appendMessage(`Network error: ${err.message}`, 'assistant', false);
    } finally {
        isGenerating = false;
        btnSend.disabled = false;
        chatInput.focus();
    }
}

btnSend.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        sendMessage();
    }
});

// Upload Logic (same as before)
const btnUpload = document.getElementById('btn-upload');
if (btnUpload) {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.log,.txt';
    btnUpload.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        appendMessage(`Uploading: ${file.name}...`, 'user');
        const loadingRow = document.createElement('div');
        loadingRow.className = 'message-row assistant';
        loadingRow.innerHTML = `<div class="avatar assistant">F</div><div class="message assistant"><div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div>`;
        chatMessages.appendChild(loadingRow);
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await fetch('/logs/analyze', { method: 'POST', credentials: 'include', body: formData });
            if (res.status === 401) { window.handleSessionExpired(); return; }
            const data = await res.json();
            chatMessages.removeChild(loadingRow);
            if (!res.ok) { appendMessage(`Error: ${data.detail}`, 'assistant', false); return; }
            appendMessage(`**Log Analysis:**\n\n${data.ai_analysis}`, 'assistant', true);
        } catch (err) {
            chatMessages.removeChild(loadingRow);
            appendMessage(`Network error: ${err.message}`, 'assistant', false);
        }
        fileInput.value = '';
    });
}
