/**
 * Web Audio API Sound Effects.
 * Generates acoustic in-cabin alert tones directly through the driver's browser speakers.
 * Rate-limited to prevent browser audio stacking or distortion.
 */

let audioCtx = null;
let activeOscillator = null;
let lastPlayTime = 0;
const MIN_PLAY_INTERVAL_MS = 600;

function getAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

export function playWarningTone() {
  const now = Date.now();
  if (now - lastPlayTime < MIN_PLAY_INTERVAL_MS) return;
  lastPlayTime = now;

  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(1500, ctx.currentTime); // 1500 Hz Warning
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.35);
  } catch (err) {
    console.debug('Audio playback issue:', err);
  }
}

export function playCriticalAlarm() {
  const now = Date.now();
  if (now - lastPlayTime < MIN_PLAY_INTERVAL_MS) return;
  lastPlayTime = now;

  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    if (activeOscillator) {
      activeOscillator.stop();
      activeOscillator = null;
    }

    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'triangle';
    osc.frequency.setValueAtTime(2500, ctx.currentTime); // 2500 Hz Urgent
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.05, ctx.currentTime + 0.6);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.6);
  } catch (err) {
    console.debug('Audio playback issue:', err);
  }
}

export function playMonitoringUnavailableTone() {
  const now = Date.now();
  if (now - lastPlayTime < 2500) return; // Rate-limit to once per 2.5s
  lastPlayTime = now;

  const ctx = getAudioContext();
  if (!ctx) return;

  try {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(800, ctx.currentTime); // 800 Hz Cautionary Chime
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.4);
  } catch (err) {
    console.debug('Audio playback issue:', err);
  }
}

export function stopAudio() {
  if (activeOscillator) {
    try {
      activeOscillator.stop();
    } catch {}
    activeOscillator = null;
  }
}
