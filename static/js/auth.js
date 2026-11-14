const authContainer = document.getElementById('auth-container');
const chatContainer = document.getElementById('chat-container');
const authError = document.getElementById('auth-error');

// On page load, check if the session cookie is still valid
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

        const contentType = res.headers.get("content-type");
        let data;
        if (contentType && contentType.indexOf("application/json") !== -1) {
            data = await res.json();
        } else {
            const text = await res.text();
            throw new Error(`Server error (${res.status})`);
        }

        if (!res.ok) {
            if (data.detail && Array.isArray(data.detail)) {
                throw new Error(data.detail[0].msg);
            }
            throw new Error(data.detail || 'Authentication failed');
        }

        showChat();
    } catch (err) {
        authError.textContent = err.message;
    }
}

document.getElementById('btn-login').addEventListener('click', () => handleAuth('login'));
document.getElementById('btn-register').addEventListener('click', () => handleAuth('register'));

// Proper Logout: destroys the HttpOnly cookie on the server
document.getElementById('btn-logout').addEventListener('click', async () => {
    try {
        await fetch('/auth/logout', { method: 'POST', credentials: 'include' });
    } catch(e) {}
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

// Expose a global function so chat.js can kick user back to login on 401
window.handleSessionExpired = () => {
    showAuth();
};
