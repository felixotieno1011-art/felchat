const authContainer = document.getElementById('auth-container');
const chatContainer = document.getElementById('chat-container');
const authError = document.getElementById('auth-error');

// On load, ask the backend if we have a valid cookie
async function checkSession() {
    try {
        const res = await fetch('/auth/me', { credentials: 'include' });
        if (res.ok) {
            showChat();
        } else {
            showAuth();
        }
    } catch (e) {
        showAuth();
    }
}

checkSession();

async function handleAuth(endpoint) {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    authError.textContent = '';

    try {
        const res = await fetch(`/auth/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Authentication failed');
        }

        showChat();
    } catch (err) {
        authError.textContent = err.message;
    }
}

document.getElementById('btn-login').addEventListener('click', () => handleAuth('login'));
document.getElementById('btn-register').addEventListener('click', () => handleAuth('register'));

document.getElementById('btn-logout').addEventListener('click', async () => {
    // Tell backend to destroy the HttpOnly cookie
    await fetch('/auth/logout', { method: 'POST', credentials: 'include' });
    showAuth();
});

function showChat() {
    authContainer.classList.add('hidden');
    chatContainer.classList.remove('hidden');
}

function showAuth() {
    authContainer.classList.remove('hidden');
    chatContainer.classList.add('hidden');
}
