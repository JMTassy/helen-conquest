// HELEN UI — Chat Client Logic

const messagesList = document.getElementById('messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatWindow = document.getElementById('chat-window');

// Load chat history on start
async function loadHistory() {
    try {
        const r = await fetch('/api/chat/history');
        const history = await r.json();
        messagesList.innerHTML = '';
        history.forEach(appendMessage);
        scrollToBottom();
    } catch (err) {
        console.error('Failed to load history:', err);
    }
}

function appendMessage(msg) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${msg.role}`;

    // Add avatar for HELEN messages
    if (msg.role === 'helen') {
        const avatar = document.createElement('img');
        avatar.src = 'helen-avatar.svg';
        avatar.className = 'message-avatar';
        avatar.alt = 'HELEN';
        msgDiv.appendChild(avatar);
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const textDiv = document.createElement('div');
    textDiv.className = 'text';
    textDiv.textContent = msg.text;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = new Date(msg.t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    contentDiv.appendChild(textDiv);
    contentDiv.appendChild(timeSpan);
    msgDiv.appendChild(contentDiv);
    messagesList.appendChild(msgDiv);
}

function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

chatForm.onsubmit = async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    // Optimistic UI: append user message immediately
    const tempUserMsg = {
        role: 'user',
        text: text,
        t: new Date().toISOString()
    };
    appendMessage(tempUserMsg);
    userInput.value = '';
    scrollToBottom();

    // Show typing indicator
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing';
    typingDiv.textContent = 'HELEN is processing...';
    messagesList.appendChild(typingDiv);
    scrollToBottom();

    try {
        const r = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });

        // Remove typing indicator
        messagesList.removeChild(typingDiv);

        if (r.ok) {
            const data = await r.json();
            appendMessage(data.helen);
            scrollToBottom();
        } else {
            console.error('Chat failed');
        }
    } catch (err) {
        console.error('Chat error:', err);
        messagesList.removeChild(typingDiv);
    }
};

// Initial load
loadHistory();

// Poll for history updates every 5 seconds (to sync other sessions)
setInterval(loadHistory, 5000);
