// ============================================================
// J.A.R.V.I.S. — Batch 1: Conversation Core
// Fast text + voice, final-sentence execution, wake/sleep/stop,
// conversation history, robust mic state, fixed scrolling chat.
// ============================================================

const SERVER = "http://localhost:5000";
const $ = id => document.getElementById(id);

const clockEl = $("clock");
const statusEl = $("sys-status");
const cpuVal = $("cpu-val");
const cpuBar = $("cpu-bar");
const memVal = $("mem-val");
const memBar = $("mem-bar");
const wakeStatus = $("wake-status");
const memoryList = $("mem-list");
const stateEl = $("state");
const chatLog = $("chat-log");
const jumpLatest = $("jump-latest");
const micBtn = $("mic-btn");
const cmdInput = $("cmd-input");
const sendBtn = $("send-btn");
const stopBtn = $("stop-btn");
const resetBtn = $("reset-btn");

const STATES = { READY:"ready", THINKING:"thinking", SPEAKING:"speaking", SLEEPING:"sleeping" };

let currentState = STATES.SLEEPING;
let activated = false;
let processing = false;
let isSpeaking = false;
let recognition = null;
let recognitionSupported = false;
let recognitionRunning = false;
let recognitionWanted = false;
let recognitionStarting = false;
let finalBuffer = "";
let commitTimer = null;
let requestController = null;
let speechGeneration = 0;
let lastSubmitted = "";
let lastSubmitTime = 0;
let userScrolledAway = false;

const COMMIT_DELAY = 420;
const DUPLICATE_WINDOW = 1800;
const REQUEST_TIMEOUT = 30000;

const WAKE_WORDS = ["hey jarvis", "okay jarvis", "ok jarvis", "jarvis"];
const SLEEP_COMMANDS = ["sleep", "go to sleep", "go sleep", "sleep mode", "stand by", "standby", "good night", "good night jarvis"];
const WAKE_COMMANDS = ["wake up", "wake up jarvis", "jarvis wake up", "come online", "go online"];
const STOP_COMMANDS = ["stop", "stop jarvis", "be quiet", "quiet", "shut up", "cancel", "cancel that"];

const VOICE_PRIORITY = [
    "Google UK English Male", "Microsoft George", "Microsoft Ryan", "Daniel", "Google UK English Female"
];

function normalize(text) {
    return String(text || "").replace(/\s+/g, " ").trim();
}

function escapeHTML(text) {
    return String(text).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\"/g,"&quot;").replace(/'/g,"&#039;");
}

function lower(text) { return normalize(text).toLowerCase(); }

function updateClock() {
    if (!clockEl) return;
    clockEl.textContent = new Date().toLocaleTimeString([], {hour:"2-digit", minute:"2-digit", second:"2-digit"});
}
updateClock();
setInterval(updateClock, 1000);

function setState(state) {
    currentState = state;
    if (stateEl) stateEl.textContent = state === STATES.SLEEPING ? "STANDBY" : state.toUpperCase();
    document.body.dataset.state = state;
    const labels = {ready:"ONLINE", thinking:"THINKING", speaking:"SPEAKING", sleeping:"STANDBY"};
    if (statusEl) statusEl.textContent = labels[state] || "ONLINE";
    if (wakeStatus && state === STATES.SLEEPING) wakeStatus.textContent = "STANDBY";
}

function isNearBottom() {
    return chatLog.scrollHeight - chatLog.scrollTop - chatLog.clientHeight < 90;
}

function scrollToLatest(force = false) {
    if (!force && userScrolledAway) return;
    requestAnimationFrame(() => { chatLog.scrollTop = chatLog.scrollHeight; });
}

function updateJumpButton() {
    userScrolledAway = !isNearBottom();
    if (jumpLatest) jumpLatest.hidden = !userScrolledAway;
}

chatLog.addEventListener("scroll", updateJumpButton, {passive:true});
jumpLatest?.addEventListener("click", () => { userScrolledAway = false; scrollToLatest(true); updateJumpButton(); });

function addMessage(role, text) {
    const message = document.createElement("div");
    message.className = `message ${role}`;
    if (role === "system") {
        message.innerHTML = `<div class="message-body">${escapeHTML(text)}</div>`;
    } else {
        message.innerHTML = `<div class="message-label">${role === "user" ? "YOU" : "J.A.R.V.I.S."}</div><div class="message-body">${escapeHTML(text)}</div>`;
    }
    chatLog.appendChild(message);
    scrollToLatest();
    return message;
}

function stopSpeechOnly() {
    speechGeneration++;
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    isSpeaking = false;
}

function chooseVoice() {
    if (!("speechSynthesis" in window)) return null;
    const voices = window.speechSynthesis.getVoices() || [];
    for (const name of VOICE_PRIORITY) {
        const exact = voices.find(v => v.name.toLowerCase().includes(name.toLowerCase()));
        if (exact) return exact;
    }
    return voices.find(v => /^en-GB/i.test(v.lang) && /male|george|ryan|daniel/i.test(v.name)) ||
           voices.find(v => /^en-GB/i.test(v.lang)) ||
           voices.find(v => /^en/i.test(v.lang)) || null;
}

function speak(text) {
    text = normalize(text);
    if (!text || !("speechSynthesis" in window)) {
        if (activated) { setState(STATES.READY); requestRecognition(); }
        return;
    }

    stopRecognition();
    stopSpeechOnly();
    const generation = speechGeneration;
    isSpeaking = true;
    setState(STATES.SPEAKING);

    const utterance = new SpeechSynthesisUtterance(text);
    const voice = chooseVoice();
    if (voice) utterance.voice = voice;
    utterance.lang = voice?.lang || "en-GB";
    utterance.rate = 0.96;
    utterance.pitch = 0.88;
    utterance.volume = 1;

    const finished = () => {
        if (generation !== speechGeneration) return;
        isSpeaking = false;
        if (activated) { setState(STATES.READY); requestRecognition(); }
        else setState(STATES.SLEEPING);
    };
    utterance.onend = finished;
    utterance.onerror = finished;
    window.speechSynthesis.speak(utterance);
}

if ("speechSynthesis" in window) window.speechSynthesis.onvoiceschanged = () => {};

function hasWakeWord(text) {
    const value = lower(text);
    return WAKE_WORDS.some(word => new RegExp(`\\b${word}\\b`, "i").test(value));
}

function removeWakeWord(text) {
    let result = text;
    for (const word of WAKE_WORDS) {
        const re = new RegExp(`\\b${word.replace(/\s+/g,"\\s+")}\\b`, "i");
        if (re.test(result)) return normalize(result.replace(re, " "));
    }
    return normalize(result);
}

function exactCommand(text, list) { return list.includes(lower(text)); }

function activate() {
    activated = true;
    if (wakeStatus) wakeStatus.textContent = "LISTENING";
    if (!processing && !isSpeaking) setState(STATES.READY);
    requestRecognition();
}

function goToSleep(speakReply = true) {
    activated = false;
    finalBuffer = "";
    clearTimeout(commitTimer);
    stopRecognition();
    stopSpeechOnly();
    setState(STATES.SLEEPING);
    if (wakeStatus) wakeStatus.textContent = "STANDBY";
    if (speakReply) speak("Standing by, Sir.");
    // speak() deliberately restarts recognition only when activated.
}

function wakeUp(speakReply = true) {
    activated = true;
    setState(STATES.READY);
    if (wakeStatus) wakeStatus.textContent = "LISTENING";
    if (speakReply) speak("I'm listening.");
    else requestRecognition();
}

function stopEverything(showMessage = true) {
    clearTimeout(commitTimer);
    finalBuffer = "";
    stopRecognition();
    stopSpeechOnly();
    if (requestController) { requestController.abort(); requestController = null; }
    processing = false;
    sendBtn.disabled = false;
    cmdInput.disabled = false;
    if (activated) { setState(STATES.READY); requestRecognition(); }
    else setState(STATES.SLEEPING);
    if (showMessage) addMessage("system", "Stopped.");
}

function setupRecognition() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
        recognitionSupported = false;
        if (wakeStatus) wakeStatus.textContent = "VOICE N/A";
        return;
    }

    recognitionSupported = true;
    recognition = new Recognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 3;
    recognition.lang = "en-GB";

    recognition.onstart = () => {
        recognitionRunning = true;
        recognitionStarting = false;
        if (activated && !processing && !isSpeaking) wakeStatus.textContent = "LISTENING";
    };

    recognition.onend = () => {
        recognitionRunning = false;
        recognitionStarting = false;
        if (recognitionWanted && activated && !processing && !isSpeaking) {
            setTimeout(requestRecognition, 120);
        }
    };

    recognition.onerror = event => {
        recognitionRunning = false;
        recognitionStarting = false;
        if (event.error === "not-allowed" || event.error === "service-not-allowed") {
            recognitionWanted = false;
            wakeStatus.textContent = "MIC BLOCKED";
            return;
        }
        if (recognitionWanted && activated && !processing && !isSpeaking) setTimeout(requestRecognition, 500);
    };

    recognition.onresult = event => {
        let finals = [];
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = normalize(result[0]?.transcript || "");
            if (result.isFinal && transcript) finals.push(transcript);
        }
        if (!finals.length) return; // Interim text can NEVER execute.
        finalBuffer = normalize(`${finalBuffer} ${finals.join(" ")}`);
        scheduleVoiceCommit();
    };
}

function requestRecognition() {
    if (!recognitionSupported || !recognition || !recognitionWanted && !activated) return;
    if (!activated || processing || isSpeaking || recognitionRunning || recognitionStarting) return;
    recognitionWanted = true;
    recognitionStarting = true;
    try { recognition.start(); }
    catch { recognitionStarting = false; }
}

function stopRecognition() {
    recognitionWanted = false;
    recognitionStarting = false;
    if (!recognition) return;
    try { recognition.stop(); } catch {}
    recognitionRunning = false;
}

function scheduleVoiceCommit() {
    clearTimeout(commitTimer);
    commitTimer = setTimeout(commitVoiceCommand, COMMIT_DELAY);
}

function commitVoiceCommand() {
    clearTimeout(commitTimer);
    commitTimer = null;
    const raw = normalize(finalBuffer);
    finalBuffer = "";
    if (!raw) return;

    if (!activated) {
        // Explicit wake commands work even without the wake phrase.
        if (exactCommand(raw, WAKE_COMMANDS)) {
            wakeUp(true);
            return;
        }
        if (!hasWakeWord(raw)) return;
        activate();
        const command = removeWakeWord(raw);
        if (!command) { speak("I'm listening."); return; }
        submitCommand(command);
        return;
    }

    const command = removeWakeWord(raw);
    if (command) submitCommand(command);
}

function submitCommand(command) {
    command = normalize(command);
    if (!command) return;

    const now = Date.now();
    if (lower(command) === lower(lastSubmitted) && now - lastSubmitTime < DUPLICATE_WINDOW) return;
    lastSubmitted = command;
    lastSubmitTime = now;

    if (exactCommand(command, SLEEP_COMMANDS)) { goToSleep(true); return; }
    if (exactCommand(command, WAKE_COMMANDS)) { wakeUp(true); return; }
    if (exactCommand(command, STOP_COMMANDS)) { stopEverything(true); return; }

    addMessage("user", command);
    sendToJarvis(command);
}

async function sendToJarvis(command) {
    if (processing) return;
    processing = true;
    clearTimeout(commitTimer);
    stopRecognition();
    setState(STATES.THINKING);
    sendBtn.disabled = true;
    cmdInput.disabled = true;

    requestController = new AbortController();
    const timeout = setTimeout(() => requestController?.abort(), REQUEST_TIMEOUT);

    try {
        const response = await fetch(`${SERVER}/chat`, {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({message:command}),
            signal:requestController.signal,
            cache:"no-store"
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        const reply = normalize(data.reply || data.response || data.message || "");
        if (!reply) throw new Error("Empty JARVIS response");
        addMessage("assistant", reply);
        speak(reply);
    } catch (error) {
        if (error.name === "AbortError") return;
        console.error("JARVIS request failed:", error);
        const reply = "I can't reach the core at the moment, Sir.";
        addMessage("assistant", reply);
        speak(reply);
    } finally {
        clearTimeout(timeout);
        processing = false;
        requestController = null;
        sendBtn.disabled = false;
        cmdInput.disabled = false;
        if (activated && !isSpeaking) requestRecognition();
    }
}

function sendTypedCommand() {
    const command = normalize(cmdInput.value);
    if (!command) return;
    cmdInput.value = "";
    if (!activated) activate();
    submitCommand(command);
}

sendBtn.addEventListener("click", sendTypedCommand);
cmdInput.addEventListener("keydown", event => {
    if (event.key === "Enter") { event.preventDefault(); sendTypedCommand(); }
});

micBtn.addEventListener("click", () => {
    if (!recognitionSupported) { addMessage("system", "Voice recognition is not supported by this browser."); return; }
    if (!activated) { wakeUp(false); return; }
    if (recognitionRunning || recognitionStarting) {
        stopRecognition();
        wakeStatus.textContent = "PAUSED";
        return;
    }
    recognitionWanted = true;
    requestRecognition();
});

stopBtn.addEventListener("click", () => stopEverything(true));

resetBtn.addEventListener("click", async () => {
    stopEverything(false);
    activated = false;
    wakeStatus.textContent = "STANDBY";
    setState(STATES.SLEEPING);
    cmdInput.value = "";
    try { await fetch(`${SERVER}/reset`, {method:"POST", cache:"no-store"}); } catch {}
    chatLog.innerHTML = "";
    addMessage("system", "J.A.R.V.I.S. reset. Standing by.");
});

document.addEventListener("click", event => {
    const button = event.target.closest("[data-command]");
    if (!button) return;
    if (!activated) activate();
    submitCommand(button.dataset.command);
});

function setMetric(valueEl, barEl, value) {
    const n = Math.max(0, Math.min(100, Number(value) || 0));
    valueEl.textContent = `${Math.round(n)}%`;
    barEl.style.width = `${n}%`;
}

async function refreshHealth() {
    try {
        const response = await fetch(`${SERVER}/health`, {cache:"no-store"});
        if (!response.ok) throw new Error("offline");
        const data = await response.json();
        statusEl.textContent = String(data.status || "ONLINE").toUpperCase();
        if (typeof data.cpu === "number") setMetric(cpuVal, cpuBar, data.cpu);
        if (typeof data.memory === "number") setMetric(memVal, memBar, data.memory);
    } catch {
        statusEl.textContent = "OFFLINE";
    }
}

async function refreshMemory() {
    try {
        const response = await fetch(`${SERVER}/memory`, {cache:"no-store"});
        if (!response.ok) return;
        const data = await response.json();
        const memories = Array.isArray(data) ? data : (data.memory || data.memories || data.items || []);
        memoryList.innerHTML = "";
        if (!memories.length) { memoryList.innerHTML = `<div class="muted">No memories loaded.</div>`; return; }
        memories.slice(0, 20).forEach(memory => {
            const item = document.createElement("div");
            item.className = "memory-item";
            item.textContent = typeof memory === "string" ? memory : (memory.text || memory.content || JSON.stringify(memory));
            memoryList.appendChild(item);
        });
    } catch {}
}

async function boot() {
    setState(STATES.SLEEPING);
    setupRecognition();
    await Promise.all([refreshHealth(), refreshMemory()]);
    setInterval(refreshHealth, 5000);
    setInterval(refreshMemory, 8000);
}

boot();
