/**
 * MediConnect Chat — WebSocket with AJAX Long-polling fallback.
 *
 * Globals expected from the template:
 *   CONSULTATION_ID, CURRENT_USER_ID, CURRENT_USER_NAME,
 *   FETCH_URL, UPLOAD_URL, CSRF
 */

(function () {
    'use strict';

    // ── State ──────────────────────────────────────────────────
    let socket = null;
    let wsConnected = false;
    let lastMessageId = 0;
    let pollInterval = null;
    let typingTimer = null;
    let isCurrentlyTyping = false;
    let pendingImageFile = null;

    // ── Init ───────────────────────────────────────────────────
    function init() {
        initLastMessageId();
        connectWebSocket();
        setupScrollBehavior();
    }

    function initLastMessageId() {
        const msgs = document.querySelectorAll('[id^="msg-"]');
        if (msgs.length) {
            const ids = Array.from(msgs).map(el => parseInt(el.id.replace('msg-', ''))).filter(Boolean);
            if (ids.length) lastMessageId = Math.max(...ids);
        }
    }

    // ── WebSocket ──────────────────────────────────────────────
    function connectWebSocket() {
        const proto = location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${proto}://${location.host}/ws/consultation/${CONSULTATION_ID}/`;
        try {
            socket = new WebSocket(wsUrl);
            socket.onopen = onOpen;
            socket.onclose = onClose;
            socket.onerror = onError;
            socket.onmessage = onMessage;
        } catch (e) {
            console.warn('[MediConnect Chat] WebSocket unavailable, falling back to AJAX polling.');
            startPolling();
        }
    }

    function onOpen() {
        wsConnected = true;
        if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
    }

    function onClose() {
        wsConnected = false;
        console.warn('[MediConnect Chat] WS closed. Starting AJAX fallback.');
        startPolling();
    }

    function onError() {
        wsConnected = false;
        startPolling();
    }

    function onMessage(event) {
        let data;
        try { data = JSON.parse(event.data); } catch (e) { return; }

        if (data.type === 'chat_message') {
            appendMessage(data, data.sender_id === CURRENT_USER_ID);
            if (data.message_id > lastMessageId) lastMessageId = data.message_id;
        } else if (data.type === 'typing_indicator') {
            if (data.sender_id !== CURRENT_USER_ID) {
                showTyping(data.sender, data.is_typing);
            }
        }
    }

    // ── AJAX Polling ────────────────────────────────────────────
    function startPolling() {
        if (pollInterval) return;
        pollInterval = setInterval(poll, 2000);
    }

    async function poll() {
        try {
            const res = await fetch(`${FETCH_URL}?since_id=${lastMessageId}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            const data = await res.json();
            if (data.status === 'ok' && data.messages) {
                data.messages.forEach(msg => {
                    if (!document.getElementById(`msg-${msg.id}`)) {
                        appendMessage(msg, msg.is_self);
                        if (msg.id > lastMessageId) lastMessageId = msg.id;
                    }
                });
            }
        } catch (e) { /* Silent fail */ }
    }

    // ── Sending Messages ────────────────────────────────────────
    window.sendMessage = function () {
        const input = document.getElementById('message-input');
        const content = input.value.trim();
        if (!content) return;
        input.value = '';
        autoResizeReset(input);
        stopTyping();

        const payload = {
            type: 'chat_message',
            content,
            sender: CURRENT_USER_NAME,
            sender_id: CURRENT_USER_ID,
        };

        if (wsConnected && socket) {
            socket.send(JSON.stringify(payload));
        } else {
            // POST via AJAX
            fetch(FETCH_URL.replace('/messages/', '/messages/').replace('/messages/', '/send/'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF, 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({ content })
            }).then(() => poll());
        }
    };

    // ── Typing Indicator ────────────────────────────────────────
    window.handleTyping = function () {
        if (!wsConnected || !socket) return;
        if (!isCurrentlyTyping) {
            isCurrentlyTyping = true;
            socket.send(JSON.stringify({ type: 'typing', sender: CURRENT_USER_NAME, sender_id: CURRENT_USER_ID, is_typing: true }));
        }
        clearTimeout(typingTimer);
        typingTimer = setTimeout(stopTyping, 2000);
    };

    function stopTyping() {
        if (isCurrentlyTyping && wsConnected && socket) {
            isCurrentlyTyping = false;
            socket.send(JSON.stringify({ type: 'typing', sender: CURRENT_USER_NAME, sender_id: CURRENT_USER_ID, is_typing: false }));
        }
    }

    function showTyping(name, isTyping) {
        const el = document.getElementById('typing-indicator');
        const nameEl = document.getElementById('typing-name');
        if (!el) return;
        if (isTyping) {
            nameEl.textContent = name;
            el.classList.remove('hidden');
            scrollBottom();
        } else {
            el.classList.add('hidden');
        }
    }

    // ── Image Upload ────────────────────────────────────────────
    window.handleImageAttach = function (input) {
        const file = input.files[0];
        if (!file) return;
        pendingImageFile = file;
        uploadImage(file);
        input.value = '';
    };

    async function uploadImage(file) {
        const formData = new FormData();
        formData.append('image', file);

        const btn = document.getElementById('send-btn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-sm"></i>';

        try {
            const res = await fetch(UPLOAD_URL, {
                method: 'POST',
                headers: { 'X-CSRFToken': CSRF, 'X-Requested-With': 'XMLHttpRequest' },
                body: formData,
            });
            const data = await res.json();
            if (data.status === 'ok') {
                // WS broadcast
                if (wsConnected && socket) {
                    socket.send(JSON.stringify({
                        type: 'image_message',
                        image_url: data.image_url,
                        sender: CURRENT_USER_NAME,
                        sender_id: CURRENT_USER_ID,
                        sent_at: data.sent_at,
                    }));
                } else {
                    appendMessage({ content: data.image_url, message_type: 'image', sender_id: CURRENT_USER_ID, sender: CURRENT_USER_NAME, sent_at: data.sent_at, message_id: data.message_id }, true);
                }
                if (data.message_id > lastMessageId) lastMessageId = data.message_id;
            } else {
                alert(data.message || 'Image upload failed.');
            }
        } catch (e) {
            alert('Upload failed. Please try again.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-paper-plane text-sm"></i>';
        }
    }

    // ── DOM Helpers ─────────────────────────────────────────────
    function appendMessage(msg, isMe) {
        const list = document.getElementById('message-list');
        if (!list) return;

        const typing = document.getElementById('typing-indicator');
        const bubble = document.createElement('div');
        bubble.id = msg.message_id ? `msg-${msg.message_id}` : '';
        bubble.className = `flex ${isMe ? 'justify-end' : 'justify-start'} animate-slide-up`;
        bubble.style.cssText = 'animation-delay:0ms;';

        const initials = CURRENT_USER_NAME.split(' ').map(p => p[0]).join('').substring(0, 2).toUpperCase();
        const authorInitials = msg.sender ? msg.sender.split(' ').map(p => p[0]).join('').substring(0, 2).toUpperCase() : '??';

        let contentHtml;
        if (msg.message_type === 'image') {
            contentHtml = `<img src="${msg.content}" alt="Shared image" class="max-w-full rounded-2xl cursor-pointer hover:opacity-90 transition-opacity" style="max-height:220px; object-fit:cover;" onclick="openLightbox('${msg.content}')">`;
        } else {
            const bgStyle = isMe
                ? 'background:linear-gradient(135deg,#0A6EBD,#3B9EE8); color:#fff;'
                : 'background:#fff; color:#0D1B2A; box-shadow:0 2px 12px rgba(10,110,189,0.08);';
            contentHtml = `<div class="px-4 py-3 rounded-2xl ${isMe ? 'rounded-br-sm' : 'rounded-bl-sm'} text-sm leading-relaxed" style="${bgStyle}">${escapeHtml(msg.content)}</div>`;
        }

        const avatarHtml = (initials) => `<div class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-auto" style="background:linear-gradient(135deg,#0A6EBD,#00C9A7);">${initials}</div>`;

        bubble.innerHTML = `
      ${!isMe ? `${avatarHtml(authorInitials)}<div class="ml-2">` : '<div>'}
        ${!isMe ? `<p class="text-xs mb-1" style="color:#8FA8C3;">${msg.sender || ''}</p>` : ''}
        ${contentHtml}
        <p class="text-xs mt-1 ${isMe ? 'text-right' : ''}" style="color:#8FA8C3;">${msg.sent_at || ''}</p>
      </div>
      ${isMe ? `<div class="ml-2">${avatarHtml(isMe ? initials : authorInitials)}</div>` : ''}
    `;

        list.insertBefore(bubble, typing);
        scrollBottom();
    }

    function escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function scrollBottom() {
        const list = document.getElementById('message-list');
        if (list) list.scrollTop = list.scrollHeight;
    }

    function setupScrollBehavior() {
        scrollBottom();
    }

    // ── Input auto-resize ─────────────────────────────────────
    window.autoResize = function (el) {
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    };
    function autoResizeReset(el) {
        el.style.height = 'auto';
    }

    window.handleEnter = function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    // ── Start ──────────────────────────────────────────────────
    document.addEventListener('DOMContentLoaded', init);
})();
