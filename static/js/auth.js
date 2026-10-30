const authContainer = document.getElementById('auth-container');
const chatContainer = document.getElementById('chat-container');
const authForm = document.getElementById('auth-form');
const authError = document.getElementById('auth-error');

// If we already have a token, go straight to chat
if (localStorage.getItem('felchat_token')) {
    showChat();
}

async function handleAuth(endpoint) {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    authError.textContent = '';

    try {
        const res = await fetch(`/auth/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Authentication failed');
        }

        localStorage.setItem('felchat_token', data.access_token);
        showChat();
    } catch (err) {
        authError.textContent = err.message;
    }
}

document.getElementById('btn-login').addEventListener('click', () => handleAuth('login'));
document.getElementById('btn-register').addEventListener('click', () => handleAuth('register'));

document.getElementById('btn-logout').addEventListener('click', () => {
    localStorage.removeItem('felchat_token');
    authContainer.classList.remove('hidden');
    chatContainer.classList.add('hidden');
});

function showChat() {
    authContainer.classList.add('hidden');
    chatContainer.classList.remove('hidden');
}
