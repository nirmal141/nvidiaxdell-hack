/**
 * Video Q&A Application - Frontend JavaScript
 */

// ===== State Management =====
const state = {
    currentVideo: null,
    videos: [],
    isProcessing: false,
    wsConnection: null
};

// ===== DOM Elements =====
const elements = {
    // Sidebar
    sidebar: document.getElementById('sidebar'),
    toggleSidebar: document.getElementById('toggleSidebar'),
    uploadZone: document.getElementById('uploadZone'),
    videoInput: document.getElementById('videoInput'),
    videoList: document.getElementById('videoList'),
    refreshLibrary: document.getElementById('refreshLibrary'),

    // Video
    videoContainer: document.getElementById('videoContainer'),
    videoPlaceholder: document.getElementById('videoPlaceholder'),
    videoPlayer: document.getElementById('videoPlayer'),
    videoTitle: document.getElementById('videoTitle'),
    videoStatus: document.getElementById('videoStatus'),
    processBtn: document.getElementById('processBtn'),
    processingOverlay: document.getElementById('processingOverlay'),
    processingStatus: document.getElementById('processingStatus'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),

    // Chat
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
    sendBtn: document.getElementById('sendBtn'),
    toastContainer: document.getElementById('toastContainer')
};

// ===== API Functions =====
const api = {
    baseUrl: '',

    async fetchVideos() {
        const response = await fetch(`${this.baseUrl}/api/videos`);
        if (!response.ok) throw new Error('Failed to fetch videos');
        return response.json();
    },

    async uploadVideo(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${this.baseUrl}/api/videos/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Failed to upload video');
        return response.json();
    },

    async processVideo(videoId) {
        const response = await fetch(`${this.baseUrl}/api/videos/${videoId}/process`, {
            method: 'POST'
        });

        if (!response.ok) throw new Error('Failed to start processing');
        return response.json();
    },

    async getVideoStatus(videoId) {
        const response = await fetch(`${this.baseUrl}/api/videos/${videoId}/status`);
        if (!response.ok) throw new Error('Failed to get status');
        return response.json();
    },

    async askQuestion(videoId, question) {
        const response = await fetch(`${this.baseUrl}/api/videos/${videoId}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_id: videoId, question })
        });

        if (!response.ok) throw new Error('Failed to get answer');
        return response.json();
    },

    async deleteVideo(videoId) {
        const response = await fetch(`${this.baseUrl}/api/videos/${videoId}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Failed to delete video');
        return response.json();
    },

    getVideoStreamUrl(videoId) {
        return `${this.baseUrl}/api/videos/${videoId}/stream`;
    },

    getThumbnailUrl(videoId) {
        return `${this.baseUrl}/api/videos/${videoId}/thumbnail`;
    }
};

// ===== Utility Functions =====
function formatDuration(seconds) {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatTimestamp(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function parseTimestamp(timestamp) {
    const match = timestamp.match(/(\d+):(\d+)/);
    if (match) {
        return parseInt(match[1]) * 60 + parseInt(match[2]);
    }
    return 0;
}

function showToast(message, type = 'info') {
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type]}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
    elements.toastContainer.appendChild(toast);

    setTimeout(() => toast.remove(), 5000);
}

// ===== Video Library Functions =====
async function loadVideoLibrary() {
    try {
        const data = await api.fetchVideos();
        state.videos = data.videos;
        renderVideoList();
    } catch (error) {
        console.error('Error loading videos:', error);
        showToast('Failed to load video library', 'error');
    }
}

function renderVideoList() {
    if (state.videos.length === 0) {
        elements.videoList.innerHTML = `
            <div class="empty-state">
                <p>No videos uploaded</p>
            </div>
        `;
        return;
    }

    elements.videoList.innerHTML = state.videos.map(video => `
        <div class="video-card ${state.currentVideo?.id === video.id ? 'active' : ''}" 
             data-video-id="${video.id}">
            <img class="video-thumb" 
                 src="${api.getThumbnailUrl(video.id)}" 
                 alt="${video.name}"
                 onerror="this.style.display='none'">
            <div class="video-info">
                <div class="video-card-title">${video.name}</div>
                <div class="video-meta">
                    <span>${formatDuration(video.duration)}</span>
                    <span class="status-badge status-${video.status}">${video.status}</span>
                </div>
            </div>
        </div>
    `).join('');

    // Add click handlers
    elements.videoList.querySelectorAll('.video-card').forEach(card => {
        card.addEventListener('click', () => {
            const videoId = card.dataset.videoId;
            const video = state.videos.find(v => v.id === videoId);
            if (video) selectVideo(video);
        });
    });
}

// ===== Video Selection & Playback =====
function selectVideo(video) {
    state.currentVideo = video;

    // Update UI
    elements.videoPlaceholder.classList.add('hidden');
    elements.videoPlayer.classList.remove('hidden');
    elements.videoPlayer.src = api.getVideoStreamUrl(video.id);
    elements.videoTitle.textContent = video.name;

    // Update status
    updateVideoStatus(video.status);

    // Enable/disable process button
    elements.processBtn.disabled = video.status === 'processing';

    // Enable chat if processed
    const isProcessed = video.status === 'completed';
    elements.chatInput.disabled = !isProcessed;
    elements.sendBtn.disabled = !isProcessed;

    if (!isProcessed) {
        elements.chatMessages.innerHTML = `
            <div class="welcome">
                <h3>Video Not Processed</h3>
                <p>Click "Process" to analyze this video and enable Q&A</p>
            </div>
        `;
    } else {
        clearChat();
    }

    // Update video cards active state
    renderVideoList();
}

function updateVideoStatus(status) {
    const statusLabels = {
        pending: '📋 Ready to process',
        processing: '⚙️ Processing...',
        completed: '✅ Processed',
        failed: '❌ Failed'
    };
    elements.videoStatus.textContent = statusLabels[status] || status;
}

function seekToTimestamp(seconds) {
    if (elements.videoPlayer) {
        elements.videoPlayer.currentTime = seconds;
        elements.videoPlayer.play();
    }
}

// ===== Upload Functions =====
function setupUploadZone() {
    elements.uploadZone.addEventListener('click', () => {
        elements.videoInput.click();
    });

    elements.videoInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    elements.uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.add('drag-over');
    });

    elements.uploadZone.addEventListener('dragleave', () => {
        elements.uploadZone.classList.remove('drag-over');
    });

    elements.uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadVideo(files[0]);
        }
    });
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        uploadVideo(file);
    }
    event.target.value = ''; // Reset input
}

async function uploadVideo(file) {
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska', 'video/webm'];
    if (!validTypes.some(t => file.type.includes(t.split('/')[1]))) {
        showToast('Unsupported video format', 'error');
        return;
    }

    showToast('Uploading video...', 'info');

    try {
        const result = await api.uploadVideo(file);

        if (result.success) {
            showToast('Video uploaded successfully!', 'success');
            await loadVideoLibrary();
            if (result.video) {
                selectVideo(result.video);
            }
        } else {
            showToast(result.error || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Failed to upload video', 'error');
    }
}

// ===== Processing Functions =====
async function startProcessing() {
    if (!state.currentVideo) return;

    state.isProcessing = true;
    elements.processBtn.disabled = true;
    elements.processingOverlay.classList.remove('hidden');
    elements.progressFill.style.width = '0%';
    elements.progressText.textContent = '0%';
    elements.processingStatus.textContent = 'Initializing...';

    // Connect to WebSocket for progress updates
    connectProgressWebSocket(state.currentVideo.id);

    try {
        await api.processVideo(state.currentVideo.id);
    } catch (error) {
        console.error('Processing error:', error);
        showToast('Failed to start processing', 'error');
        hideProcessingOverlay();
    }
}

function connectProgressWebSocket(videoId) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/progress/${videoId}`;

    state.wsConnection = new WebSocket(wsUrl);

    state.wsConnection.onopen = () => {
        console.log('WebSocket connected');
    };

    state.wsConnection.onmessage = (event) => {
        const progress = JSON.parse(event.data);
        updateProgress(progress);
    };

    state.wsConnection.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    state.wsConnection.onclose = () => {
        console.log('WebSocket disconnected');
        // Poll for status if WebSocket closes
        if (state.isProcessing) {
            pollProcessingStatus(videoId);
        }
    };
}

function updateProgress(progress) {
    const percent = progress.total_frames > 0
        ? Math.round((progress.current_frame / progress.total_frames) * 100)
        : 0;

    elements.progressFill.style.width = `${percent}%`;
    elements.progressText.textContent = `${percent}%`;
    elements.processingStatus.textContent = progress.message || `Processing frame ${progress.current_frame}/${progress.total_frames}`;

    if (progress.status === 'completed') {
        handleProcessingComplete();
    } else if (progress.status === 'failed') {
        handleProcessingFailed(progress.message);
    }
}

async function pollProcessingStatus(videoId) {
    const poll = async () => {
        try {
            const status = await api.getVideoStatus(videoId);
            updateProgress(status);

            if (status.status === 'processing') {
                setTimeout(poll, 2000);
            }
        } catch (error) {
            console.error('Status poll error:', error);
        }
    };

    poll();
}

function handleProcessingComplete() {
    state.isProcessing = false;
    hideProcessingOverlay();
    showToast('Video processed successfully!', 'success');

    // Update video status
    if (state.currentVideo) {
        state.currentVideo.status = 'completed';
        updateVideoStatus('completed');
        elements.chatInput.disabled = false;
        elements.sendBtn.disabled = false;
        clearChat();
    }

    loadVideoLibrary();

    if (state.wsConnection) {
        state.wsConnection.close();
    }
}

function handleProcessingFailed(message) {
    state.isProcessing = false;
    hideProcessingOverlay();
    showToast(`Processing failed: ${message}`, 'error');
    elements.processBtn.disabled = false;

    if (state.wsConnection) {
        state.wsConnection.close();
    }
}

function hideProcessingOverlay() {
    elements.processingOverlay.classList.add('hidden');
    elements.processBtn.disabled = false;
}

// ===== Chat Functions =====
function clearChat() {
    elements.chatMessages.innerHTML = `
        <div class="welcome">
            <h3>Ready to Answer Questions</h3>
            <p>Ask me anything about this video!</p>
            <div class="suggestions">
                <button class="example-btn" data-question="What happens in this video?">What happens in this video?</button>
                <button class="example-btn" data-question="Who appears in the video?">Who appears in the video?</button>
                <button class="example-btn" data-question="Describe the key moments">Describe the key moments</button>
            </div>
        </div>
    `;

    // Add example question handlers
    elements.chatMessages.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            elements.chatInput.value = btn.dataset.question;
            sendMessage();
        });
    });
}

function addMessage(content, role, sources = []) {
    // Remove welcome message if present
    const welcome = elements.chatMessages.querySelector('.welcome');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const avatar = role === 'user' ? '👤' : '🤖';

    // Parse timestamps in content and make them clickable
    let processedContent = content;
    if (role === 'assistant') {
        processedContent = content.replace(/\[(\d{1,2}:\d{2})\]/g, (match, time) => {
            const seconds = parseTimestamp(time);
            return `<span class="timestamp-link" data-seconds="${seconds}">[${time}]</span>`;
        });
    }

    let sourcesHtml = '';
    if (sources.length > 0) {
        sourcesHtml = `
            <div class="message-sources">
                <div class="sources-label">📍 Source moments:</div>
                ${sources.map(s => `
                    <div class="source-item">
                        <span class="source-timestamp" data-seconds="${s.timestamp}">[${formatTimestamp(s.timestamp)}]</span>
                        <span class="source-description">${s.description.substring(0, 100)}...</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${processedContent}
            ${sourcesHtml}
        </div>
    `;

    elements.chatMessages.appendChild(messageDiv);

    // Add click handlers for timestamps
    messageDiv.querySelectorAll('.timestamp-link, .source-timestamp').forEach(el => {
        el.addEventListener('click', () => {
            const seconds = parseFloat(el.dataset.seconds);
            seekToTimestamp(seconds);
        });
    });

    // Scroll to bottom
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

async function sendMessage() {
    const question = elements.chatInput.value.trim();
    if (!question || !state.currentVideo) return;

    // Add user message
    addMessage(question, 'user');
    elements.chatInput.value = '';

    // Disable input while processing
    elements.chatInput.disabled = true;
    elements.sendBtn.disabled = true;

    try {
        const response = await api.askQuestion(state.currentVideo.id, question);
        addMessage(response.answer, 'assistant', response.sources);
    } catch (error) {
        console.error('Question error:', error);
        addMessage('Sorry, I encountered an error processing your question. Please try again.', 'assistant');
    } finally {
        elements.chatInput.disabled = false;
        elements.sendBtn.disabled = false;
        elements.chatInput.focus();
    }
}

// ===== Event Listeners =====
function setupEventListeners() {
    // Sidebar toggle (removed - no toggle button in new design)
    if (elements.toggleSidebar) {
        elements.toggleSidebar.addEventListener('click', () => {
            elements.sidebar.classList.toggle('collapsed');
        });
    }

    // Refresh library
    elements.refreshLibrary.addEventListener('click', loadVideoLibrary);

    // Process button
    elements.processBtn.addEventListener('click', startProcessing);

    // Chat input
    elements.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Auto-resize textarea
    elements.chatInput.addEventListener('input', () => {
        elements.chatInput.style.height = 'auto';
        elements.chatInput.style.height = elements.chatInput.scrollHeight + 'px';
    });

    // Send button
    elements.sendBtn.addEventListener('click', sendMessage);

    // Example questions
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!elements.chatInput.disabled) {
                elements.chatInput.value = btn.dataset.question;
                sendMessage();
            }
        });
    });
}

// ===== Initialization =====
function init() {
    setupUploadZone();
    setupEventListeners();
    loadVideoLibrary();
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
