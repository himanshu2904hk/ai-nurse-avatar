// ╔══════════════════════════════════════════════════════════════════════════╗
// ║                      DAILY FRAME LIFECYCLE                               ║
// ║                                                                          ║
// ║   Creates, joins, and destroys the Daily WebRTC iframe.                  ║
// ╚══════════════════════════════════════════════════════════════════════════╝

import { log } from './logger.js';

let callFrame = null;

export function createFrame(videoContainer) {
    // This DailyIframe object is the WebRTC engine
    callFrame = DailyIframe.createFrame(videoContainer, {
        showLeaveButton: false,
        showFullscreenButton: false,
        iframeStyle: {
            position: 'absolute',
            top: '0',
            left: '0',
            width: '100%',
            height: '100%',
            border: 'none'
        }
    });
    return callFrame;
}

export async function joinRoom(url) {
    if (!callFrame) return;
    log(`Joining room: ${url}`);
    try {
        await callFrame.join({ url });
        log('Successfully joined Daily room!', 'success');
    } catch (err) {
        log(`Join error: ${err.message}`, 'error');
        throw err;
    }
}

export async function leaveAndDestroy() {
    if (!callFrame) return;
    await callFrame.leave();
    callFrame.destroy();
    callFrame = null;
}

export function getFrame() {
    return callFrame;
}
