// ╔══════════════════════════════════════════════════════════════════════════╗
// ║                         UI CONTROLLER                                    ║
// ║                                                                          ║
// ║   Manages start/stop button states, container visibility,                ║
// ║   and log panel height sync.                                             ║
// ╚══════════════════════════════════════════════════════════════════════════╝

const startContainer = document.getElementById('start-container');
const videoContainer = document.getElementById('video-container');
const stopBtn = document.getElementById('btn-stop');


export function showLoading() {
    startContainer.innerHTML = '<p class="info">Creating conversation...</p>';
}

export function showVideo() {
    videoContainer.classList.remove('hidden');
    stopBtn.classList.remove('hidden');
    startContainer.classList.add('hidden');
}

export function showStopping() {
    stopBtn.textContent = 'Stopping...';
}

export function resetToStart() {
    videoContainer.innerHTML = '';
    videoContainer.classList.add('hidden');
    stopBtn.classList.add('hidden');
    stopBtn.textContent = 'Stop & Save Credits';
    startContainer.innerHTML = `
        <p class="info">Conversation ended. Click to start again.</p>
        <button type="button" class="start-btn" onclick="location.reload()">Start New Conversation</button>
    `;
    startContainer.classList.remove('hidden');
}

export function showError(message) {
    startContainer.innerHTML = `
        <p class="info" style="color: #f66;">Error: ${message}</p>
        <button type="button" class="start-btn" onclick="location.reload()">Try Again</button>
    `;
}

export function getVideoContainer() {
    return videoContainer;
}

