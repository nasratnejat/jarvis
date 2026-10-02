// ============================================================
// J.A.R.V.I.S. — app.js
// TRUE STANDBY / WAKE-WORD CONTROL
// STREAMING RESPONSES
// CLEAN SPEECH OUTPUT
// ============================================================

const SERVER = "http://127.0.0.1:5000";

const chatLog = document.getElementById("chat-log");
const cmdInput = document.getElementById("cmd-input");
const core = document.getElementById("core");
const stateEl = document.getElementById("state");
const micBtn = document.getElementById("mic-btn");
const stopBtn = document.getElementById("stop-btn");
const wakeStatus = document.getElementById("wake-status");
const memList = document.getElementById("mem-list");

// ============================================================
// STATE
// ============================================================

let mode = "sleeping";
let activated = false;
let finalBuffer = "";
let cmdTimer = null;
let isSpeaking = false;
let jarvisVoice = null;
let activeRequest = null;
let recognitionStarting = false;
let recognitionRunning = false;
let recognitionRestartTimer = null;

const spokenTimerEvents = new Map();

// ============================================================
// VOICE
// ============================================================

const LANG = "en-US";

const WAKE_RE =
  /\b(?:(?:hey|ok|okay)\s+)?(?:jarvis|jarvas|jervis|jarvi|gervais|travis|charvis|jarvus|wake\s+up)\b/gi;

const SLEEP_RE =
  /\b(?:sleep|go\s+to\s+sleep|go\s+sleep|sleep\s+mode|go\s+offline|stand\s+by|standby|good\s+night|jarvis\s+sleep)\b/gi;

// ============================================================
// PERSONALITY
// ============================================================

const JARVIS_LINES = {
  wake: [
    "Yes, Sir.",
    "I'm listening.",
    "Go ahead, Sir.",
    "Standing by, Sir.",
    "Understood.",
  ],

  boot: [
    "Systems online.",
    "All systems operational.",
    "Systems ready, Sir.",
    "Online and standing by, Sir.",
  ],

  thinking: [
    "Analyzing.",
    "Processing.",
    "One moment, Sir.",
    "Checking.",
    "Working on it.",
  ],

  offline: [
    "Going offline, Sir.",
    "Entering sleep mode.",
    "Standing by, Sir.",
    "Going quiet, Sir.",
  ],
};

function randomLine(group) {
  const lines = JARVIS_LINES[group];

  if (!lines || !lines.length) {
    return "";
  }

  return lines[Math.floor(Math.random() * lines.length)];
}

// ============================================================
// SILENT METADATA
// ============================================================

function removeSilentMetadata(text) {
  return String(text || "")
    .replace(/\*\*\*[\s\S]*?\*\*\*/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

// ============================================================
// SPEECH CLEANER
//
// IMPORTANT:
// Displayed text is NOT modified.
// Only text sent to SpeechSynthesis is cleaned.
//
// This prevents JARVIS from saying:
// "asterisk asterisk"
// "underscore"
// "backtick"
// "hash"
// and similar Markdown punctuation.
// ============================================================

function cleanForSpeech(text) {
  let clean = String(text || "");

  // Remove silent metadata blocks first.
  clean = clean.replace(/\*\*\*[\s\S]*?\*\*\*/g, " ");

  // Markdown links:
  // [Apple website](https://apple.com)
  // becomes:
  // Apple website
  clean = clean.replace(/\[([^\]]+)\]\((?:https?:\/\/)?[^)]+\)/g, "$1");

  // Remove fenced-code markers but keep code text.
  clean = clean.replace(/```/g, " ");

  // Markdown emphasis characters.
  clean = clean.replace(/[*_~`]/g, "");

  // Markdown headings.
  clean = clean.replace(/^\s*#{1,6}\s+/gm, "");

  // Markdown bullet markers.
  clean = clean.replace(/^\s*[-•]\s+/gm, "");

  // Markdown blockquote marker.
  clean = clean.replace(/^\s*>\s+/gm, "");

  // Table separators.
  clean = clean.replace(/^\s*\|[\s|:-]+\|\s*$/gm, " ");

  // Remaining pipe characters from simple Markdown tables.
  clean = clean.replace(/\|/g, " ");

  // Repeated punctuation that doesn't need to be spoken.
  clean = clean.replace(/:{2,}/g, " ");

  clean = clean.replace(/-{3,}/g, " ");

  clean = clean.replace(/={3,}/g, " ");

  // Keep normal punctuation because it improves speech rhythm.
  clean = clean.replace(/\s+/g, " ").trim();

  return clean;
}

// ============================================================
// TEXT
// ============================================================

function jarvisize(text) {
  const clean = removeSilentMetadata(text);

  if (!clean) {
    return "Nothing to report.";
  }

  return clean;
}

// ============================================================
// COMMAND NORMALIZATION
// ============================================================

function normalizeCommand(text) {
  let c = removeSilentMetadata(text).toLowerCase().trim();

  c = c.replace(/[.,!?;:]+/g, " ");
  c = c.replace(/\s+/g, " ").trim();

  const replacements = [
    [/\bnot\s+pad\b/g, "notepad"],
    [/\bnote\s+pad\b/g, "notepad"],
    [/\bnote-pad\b/g, "notepad"],
    [/\bnotepadd\b/g, "notepad"],
    [/\bcrhome\b/g, "chrome"],
    [/\bchrom\b/g, "chrome"],
    [/\byou\s+tube\b/g, "youtube"],
    [/\bspot\s+ify\b/g, "spotify"],
    [/\bspotty\s+fy\b/g, "spotify"],
    [/\bdis\s+cord\b/g, "discord"],
    [/\bcalc\b/g, "calculator"],
    [/\btask\s+man\b/g, "task manager"],
    [/\bvs\s+code\b/g, "vscode"],
    [/\bpower\s+shell\b/g, "powershell"],
    [/\bfile\s+explorer\b/g, "file explorer"],
  ];

  for (const [pattern, replacement] of replacements) {
    c = c.replace(pattern, replacement);
  }

  return c.replace(/\s+/g, " ").trim();
}

// ============================================================
// CLOCK
// ============================================================

function updateClock() {
  const clock = document.getElementById("clock");

  if (!clock) {
    return;
  }

  const n = new Date();

  clock.textContent = [n.getHours(), n.getMinutes(), n.getSeconds()]
    .map((x) => String(x).padStart(2, "0"))
    .join(":");
}

updateClock();

setInterval(updateClock, 1000);

// ============================================================
// HEALTH
// ============================================================

async function refreshHealth() {
  try {
    const response = await fetch(`${SERVER}/health`, {
      signal: AbortSignal.timeout(3000),
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Health HTTP ${response.status}`);
    }

    const data = await response.json();

    if (data.online) {
      const cpu = document.getElementById("cpu-val");

      const mem = document.getElementById("mem-val");

      if (cpu) {
        cpu.textContent = "ONLINE";
      }

      if (mem) {
        mem.textContent = data.openai_configured ? "READY" : "NO API KEY";
      }
    }
  } catch (err) {
    console.warn("[JARVIS] Health check failed:", err.message);
  }
}

refreshHealth();

setInterval(refreshHealth, 5000);

// ============================================================
// STATE
// ============================================================

function setState(m, label) {
  mode = m;

  if (stateEl) {
    stateEl.textContent = label;
  }

  const coreState = m === "sleeping" ? "" : m === "ready" ? "listening" : m;

  if (core) {
    core.className = "core " + coreState;
  }

  if (micBtn) {
    micBtn.className = "mic" + (m === "ready" ? " active" : "");
  }

  const stateLabels = {
    sleeping: "STANDBY",
    ready: "LISTENING",
    thinking: "CALCULATING",
    speaking: "RESPONDING",
  };

  if (wakeStatus) {
    wakeStatus.textContent = stateLabels[m] || String(m).toUpperCase();
  }
}

// ============================================================
// CHAT
// ============================================================

function isNearBottom() {
  if (!chatLog) {
    return true;
  }

  const distance =
    chatLog.scrollHeight - chatLog.scrollTop - chatLog.clientHeight;

  return distance < 120;
}

function scrollToLatest() {
  if (!chatLog) {
    return;
  }

  chatLog.scrollTop = chatLog.scrollHeight;
}

function addMsg(role, html) {
  if (!chatLog) {
    return null;
  }

  const div = document.createElement("div");

  div.className = `msg ${role}`;

  div.innerHTML = `
    <div class="lbl">
      ${role === "user" ? "YOU" : "JARVIS"}
    </div>

    <div class="txt">
      ${html}
    </div>
  `;

  const shouldScroll = isNearBottom();

  chatLog.appendChild(div);

  if (shouldScroll) {
    scrollToLatest();
  }

  return div;
}

// ============================================================
// JARVIS REPLY DISPLAY
// ============================================================

function showJarvisReply(messageEl, text) {
  const clean = removeSilentMetadata(text);

  if (!clean) {
    console.warn("[JARVIS] Empty reply received.");

    return;
  }

  if (messageEl) {
    const output = messageEl.querySelector(".txt");

    if (output) {
      // Preserve original response on screen.
      output.textContent = clean;

      output.style.display = "block";

      output.style.visibility = "visible";

      output.style.opacity = "1";
    } else {
      messageEl.innerHTML = `
        <div class="lbl">JARVIS</div>
        <div class="txt"></div>
      `;

      const newOutput = messageEl.querySelector(".txt");

      if (newOutput) {
        newOutput.textContent = clean;
      }
    }
  } else {
    addMsg("jarvis", escapeHtml(clean));
  }

  setTimeout(scrollToLatest, 0);
}

// ============================================================
// VOICE LOADER
// ============================================================

function loadVoice() {
  if (!window.speechSynthesis) {
    return;
  }

  const voices = speechSynthesis.getVoices();

  const picks = [
    "Google UK English Male",
    "Microsoft George - English (United Kingdom)",
    "Microsoft Ryan Online (Natural) - English (United Kingdom)",
    "Microsoft George Online (Natural) - English (United Kingdom)",
    "Microsoft David Desktop - English (United States)",
    "Google US English Male",
    "Daniel",
  ];

  for (const name of picks) {
    const voice = voices.find((v) => v.name === name);

    if (voice) {
      jarvisVoice = voice;

      console.log("JARVIS voice:", voice.name);

      return;
    }
  }

  jarvisVoice =
    voices.find(
      (v) =>
        v.lang &&
        v.lang.startsWith("en") &&
        /male|george|david|daniel|ryan/i.test(v.name),
    ) || null;

  if (jarvisVoice) {
    console.log("JARVIS fallback voice:", jarvisVoice.name);
  }
}

if (window.speechSynthesis) {
  speechSynthesis.onvoiceschanged = loadVoice;

  loadVoice();
}

// ============================================================
// SPEECH QUEUE
// ============================================================

const speakQueue = [];
let queueRunning = false;

function speakQueued(text) {
  const cleanText = cleanForSpeech(text);

  if (!cleanText) {
    return;
  }

  speakQueue.push(cleanText);

  if (!queueRunning) {
    drainQueue();
  }
}

function drainQueue() {
  if (!speakQueue.length) {
    queueRunning = false;
    isSpeaking = false;

    if (stopBtn) {
      stopBtn.style.display = "none";
    }

    setTimeout(startRecognition, 100);

    return;
  }

  queueRunning = true;
  isSpeaking = true;

  abortRecognition();

  if (stopBtn) {
    stopBtn.style.display = "flex";
  }

  const text = cleanForSpeech(speakQueue.shift());

  if (!text) {
    drainQueue();
    return;
  }

  const utterance = new SpeechSynthesisUtterance(text);

  // ========================================================
  // VOICE SETTINGS — UNCHANGED
  // ========================================================

  utterance.rate = 1.15;
  utterance.pitch = 0.86;
  utterance.volume = 1;

  if (jarvisVoice) {
    utterance.voice = jarvisVoice;
  }

  utterance.onend = drainQueue;

  utterance.onerror = drainQueue;

  speechSynthesis.speak(utterance);
}

// ============================================================
// SPEAK
// ============================================================

function speak(text) {
  const cleanText = cleanForSpeech(text);

  if (!cleanText) {
    return;
  }

  if (!window.speechSynthesis) {
    setState("ready", "LISTENING");

    return;
  }

  speakQueue.length = 0;

  speechSynthesis.cancel();

  setState("speaking", "RESPONDING...");

  speakQueued(cleanText);
}

// ============================================================
// STOP SPEAKING
// ============================================================

function stopSpeaking() {
  speakQueue.length = 0;
  queueRunning = false;

  if (activeRequest) {
    try {
      activeRequest.abort();
    } catch (e) {}

    activeRequest = null;
  }

  if (window.speechSynthesis) {
    speechSynthesis.cancel();
  }

  isSpeaking = false;

  if (stopBtn) {
    stopBtn.style.display = "none";
  }

  if (activated) {
    setState("ready", "LISTENING");
  } else {
    setState("sleeping", "STANDBY");
  }

  setTimeout(startRecognition, 100);
}

if (stopBtn) {
  stopBtn.addEventListener("click", stopSpeaking);
}

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    stopSpeaking();
  }
});

// ============================================================
// SSE STREAM READER
// ============================================================

async function readJarvisStream(response, messageEl) {
  const contentType = response.headers.get("content-type") || "";

  if (!contentType.includes("text/event-stream")) {
    const data = await response.json();

    const rawReply = data.reply ?? data.response ?? data.text ?? "";

    const reply = removeSilentMetadata(rawReply);

    if (!reply) {
      throw new Error("The server returned no usable response.");
    }

    showJarvisReply(messageEl, reply);

    return reply;
  }

  if (!response.body) {
    throw new Error("Streaming is not available in this browser.");
  }

  const reader = response.body.getReader();

  const decoder = new TextDecoder("utf-8");

  let buffer = "";
  let fullReply = "";
  let finalReply = "";
  let streamError = null;

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, {
      stream: true,
    });

    while (true) {
      const separatorIndex = buffer.indexOf("\n\n");

      if (separatorIndex === -1) {
        break;
      }

      const eventBlock = buffer.slice(0, separatorIndex);

      buffer = buffer.slice(separatorIndex + 2);

      const lines = eventBlock.split(/\r?\n/);

      let dataText = "";

      for (const line of lines) {
        if (line.startsWith("data:")) {
          dataText += line.slice(5).replace(/^\s+/, "");
        }
      }

      if (!dataText) {
        continue;
      }

      let eventData;

      try {
        eventData = JSON.parse(dataText);
      } catch (error) {
        console.warn("[JARVIS] Invalid stream event:", dataText);

        continue;
      }

      if (eventData.type === "delta") {
        const delta = String(eventData.text || "");

        if (!delta) {
          continue;
        }

        fullReply += delta;

        // IMPORTANT:
        // Display the original response.
        // Do not speech-clean the visible text.
        showJarvisReply(messageEl, fullReply);
      } else if (eventData.type === "done") {
        finalReply = removeSilentMetadata(eventData.reply || fullReply);

        if (finalReply) {
          showJarvisReply(messageEl, finalReply);
        }
      } else if (eventData.type === "error") {
        streamError = removeSilentMetadata(
          eventData.error || "Streaming error, Sir.",
        );
      }
    }
  }

  buffer += decoder.decode();

  if (streamError) {
    throw new Error(streamError);
  }

  const reply = finalReply || removeSilentMetadata(fullReply);

  if (!reply) {
    throw new Error("I received no usable response from the server, Sir.");
  }

  return reply;
}

// ============================================================
// SEND MESSAGE
// ============================================================

async function sendMessage(text) {
  text = normalizeCommand(removeSilentMetadata(text));

  if (!text) {
    setState("ready", "LISTENING");

    return;
  }

  console.log("[JARVIS] Sending command:", text);

  console.log("[JARVIS] POST:", `${SERVER}/stream`);

  addMsg("user", escapeHtml(text));

  setState("thinking", randomLine("thinking").toUpperCase());

  const messageEl = addMsg(
    "jarvis",
    `
        <span class="typing">
          <span>.</span>
          <span>.</span>
          <span>.</span>
        </span>
      `,
  );

  try {
    activeRequest = new AbortController();

    const response = await fetch(`${SERVER}/stream`, {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },

      body: JSON.stringify({
        message: text,
      }),

      signal: activeRequest.signal,

      cache: "no-store",
    });

    console.log("[JARVIS] Server HTTP:", response.status);

    if (!response.ok) {
      let serverMessage = `Server returned HTTP ${response.status}.`;

      try {
        const errorData = await response.json();

        console.error("[JARVIS] Server error:", errorData);

        serverMessage = errorData.reply || errorData.error || serverMessage;
      } catch (e) {
        console.warn("[JARVIS] Could not parse server error JSON.");
      }

      serverMessage = removeSilentMetadata(serverMessage);

      showJarvisReply(messageEl, serverMessage);

      speak(serverMessage);

      return;
    }

    const reply = await readJarvisStream(response, messageEl);

    console.log("[JARVIS] Final reply:", reply);

    // Speech gets cleaned Markdown.
    // The visible answer remains untouched.
    speak(reply);

    refreshMemory();
  } catch (err) {
    console.error("[JARVIS] Request failed:", err);

    let message;

    if (err.name === "AbortError") {
      message = "Request cancelled, Sir.";
    } else {
      message = err.message || "I couldn't reach the JARVIS server, Sir.";
    }

    message = removeSilentMetadata(message);

    showJarvisReply(messageEl, message);

    speak(message);
  } finally {
    activeRequest = null;
  }
}

// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// ============================================================
// SPEECH RECOGNITION
// ============================================================

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;

let rec = null;

// ============================================================
// BUFFER
// ============================================================

function clearSpeechBuffer() {
  finalBuffer = "";

  clearTimeout(cmdTimer);

  cmdTimer = null;

  if (cmdInput) {
    cmdInput.value = "";
  }
}

// ============================================================
// WAKE
// ============================================================

function containsWakeWord(text) {
  const clean = removeSilentMetadata(text);

  WAKE_RE.lastIndex = 0;

  return WAKE_RE.test(clean);
}

function removeWakeWord(text) {
  let clean = removeSilentMetadata(text);

  WAKE_RE.lastIndex = 0;

  clean = clean.replace(WAKE_RE, " ");

  return clean.replace(/\s+/g, " ").trim();
}

// ============================================================
// SLEEP
// ============================================================

function containsSleepCommand(text) {
  const clean = removeSilentMetadata(text);

  SLEEP_RE.lastIndex = 0;

  return SLEEP_RE.test(clean);
}

// ============================================================
// RECOGNITION START
// ============================================================

function startRecognition() {
  if (!SR || !rec) {
    return;
  }

  if (isSpeaking) {
    return;
  }

  if (mode === "thinking") {
    return;
  }

  if (recognitionRunning) {
    return;
  }

  if (recognitionStarting) {
    return;
  }

  recognitionStarting = true;

  try {
    rec.start();
  } catch (error) {
    recognitionStarting = false;

    console.debug("Recognition start:", error.message);

    scheduleRecognitionRestart();
  }
}

// ============================================================
// RECOGNITION RESTART
// ============================================================

function scheduleRecognitionRestart() {
  clearTimeout(recognitionRestartTimer);

  recognitionRestartTimer = setTimeout(() => {
    recognitionRestartTimer = null;

    if (!isSpeaking) {
      startRecognition();
    }
  }, 100);
}

// ============================================================
// ABORT RECOGNITION
// ============================================================

function abortRecognition() {
  clearTimeout(recognitionRestartTimer);

  recognitionRestartTimer = null;

  if (!rec) {
    return;
  }

  recognitionStarting = false;

  recognitionRunning = false;

  try {
    rec.abort();
  } catch (error) {}
}

// ============================================================
// SLEEP
// ============================================================

function goSleep() {
  console.log("JARVIS entering true standby.");

  activated = false;

  clearSpeechBuffer();

  if (activeRequest) {
    try {
      activeRequest.abort();
    } catch (e) {}

    activeRequest = null;
  }

  abortRecognition();

  speakQueue.length = 0;

  queueRunning = false;

  if (window.speechSynthesis) {
    speechSynthesis.cancel();
  }

  const goodbye = new SpeechSynthesisUtterance(
    cleanForSpeech(randomLine("offline")),
  );

  goodbye.rate = 1.02;
  goodbye.pitch = 0.84;
  goodbye.volume = 1;

  if (jarvisVoice) {
    goodbye.voice = jarvisVoice;
  }

  isSpeaking = true;

  setState("speaking", "POWERING DOWN...");

  if (stopBtn) {
    stopBtn.style.display = "flex";
  }

  const finished = () => {
    isSpeaking = false;

    if (stopBtn) {
      stopBtn.style.display = "none";
    }

    setState("sleeping", "STANDBY");

    clearSpeechBuffer();

    setTimeout(() => {
      if (!activated && !isSpeaking) {
        startRecognition();
      }
    }, 150);
  };

  goodbye.onend = finished;

  goodbye.onerror = finished;

  speechSynthesis.speak(goodbye);
}

// ============================================================
// SPEECH ENGINE
// ============================================================

if (SR) {
  rec = new SR();

  rec.continuous = true;
  rec.interimResults = true;
  rec.maxAlternatives = 3;
  rec.lang = LANG;

  rec.onstart = () => {
    recognitionStarting = false;

    recognitionRunning = true;

    console.log(
      activated ? "Command recognition ready." : "Wake-word recognition ready.",
    );
  };

  rec.onresult = (event) => {
    if (isSpeaking) {
      return;
    }

    let newFinalText = "";
    let interimText = "";
    let hasFinalResult = false;

    let wokeFromStandby = false;

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];

      if (!result || !result[0]) {
        continue;
      }

      const transcript = removeSilentMetadata(result[0].transcript);

      if (!transcript) {
        continue;
      }

      // ----------------------------------------------
      // SLEEPING
      // ----------------------------------------------

      if (!activated) {
        if (containsWakeWord(transcript)) {
          console.log("Wake word detected:", transcript);

          activated = true;

          wokeFromStandby = true;

          clearSpeechBuffer();

          const afterWake = removeWakeWord(transcript);

          setState("ready", "LISTENING");

          if (result.isFinal) {
            if (afterWake) {
              finalBuffer = afterWake;
            } else {
              speak(randomLine("wake"));

              return;
            }
          } else {
            if (cmdInput) {
              cmdInput.value = afterWake || "";
            }

            if (!afterWake) {
              return;
            }
          }
        } else {
          return;
        }
      }

      // ----------------------------------------------
      // AWAKE
      // ----------------------------------------------

      if (result.isFinal) {
        newFinalText += (newFinalText ? " " : "") + transcript;

        hasFinalResult = true;
      } else {
        interimText += (interimText ? " " : "") + transcript;
      }
    }

    if (wokeFromStandby && newFinalText) {
      newFinalText = removeWakeWord(newFinalText);
    }

    // ----------------------------------------------
    // SLEEP COMMAND
    // ----------------------------------------------

    if (activated && containsSleepCommand(newFinalText || interimText)) {
      if (hasFinalResult) {
        goSleep();
      }

      return;
    }

    // ----------------------------------------------
    // STORE AWAKE SPEECH
    // ----------------------------------------------

    if (newFinalText) {
      finalBuffer += (finalBuffer ? " " : "") + newFinalText;

      finalBuffer = removeSilentMetadata(finalBuffer);
    }

    const combinedText = removeSilentMetadata(
      finalBuffer + (interimText ? " " + interimText : ""),
    );

    if (!combinedText) {
      return;
    }

    if (cmdInput) {
      cmdInput.value = combinedText;
    }

    if (!hasFinalResult) {
      return;
    }

    const finalCommand = normalizeCommand(finalBuffer);

    if (!finalCommand) {
      clearSpeechBuffer();
      return;
    }

    console.log("Sending command:", finalCommand);

    clearSpeechBuffer();

    abortRecognition();

    sendMessage(finalCommand);
  };

  rec.onerror = (event) => {
    recognitionStarting = false;

    recognitionRunning = false;

    console.warn("Speech recognition:", event.error);

    if (
      event.error === "not-allowed" ||
      event.error === "service-not-allowed"
    ) {
      if (wakeStatus) {
        wakeStatus.textContent = "MIC BLOCKED";

        wakeStatus.style.color = "#ff4400";
      }

      return;
    }

    if (event.error === "network") {
      if (wakeStatus) {
        wakeStatus.textContent = "VOICE RETRY";

        wakeStatus.style.color = "#ffaa00";
      }
    }

    scheduleRecognitionRestart();
  };

  rec.onend = () => {
    recognitionStarting = false;

    recognitionRunning = false;

    if (!isSpeaking && mode !== "thinking") {
      scheduleRecognitionRestart();
    }
  };

  if (micBtn) {
    micBtn.addEventListener("click", () => {
      activated = true;

      clearSpeechBuffer();

      setState("ready", "LISTENING");

      speak(randomLine("wake"));
    });
  }

  setTimeout(startRecognition, 150);

  setTimeout(startRecognition, 500);

  setTimeout(startRecognition, 1000);

  document.addEventListener(
    "click",
    () => {
      startRecognition();

      setTimeout(startRecognition, 150);

      setTimeout(startRecognition, 400);
    },
    {
      once: true,
    },
  );
} else {
  if (wakeStatus) {
    wakeStatus.textContent = "USE CHROME";

    wakeStatus.style.color = "#ff4400";
  }
}

// ============================================================
// TYPED INPUT
// ============================================================

async function sendTyped() {
  if (!cmdInput) {
    return;
  }

  const text = removeSilentMetadata(cmdInput.value).trim();

  if (!text) {
    return;
  }

  clearTimeout(cmdTimer);

  abortRecognition();

  cmdInput.value = "";

  activated = true;

  setState("ready", "LISTENING");

  await sendMessage(text);
}

const sendButton = document.getElementById("send-btn");

if (sendButton) {
  sendButton.addEventListener("click", sendTyped);
}

if (cmdInput) {
  cmdInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();

      sendTyped();
    }
  });
}

// ============================================================
// RESET
// ============================================================

const resetButton = document.getElementById("reset-btn");

if (resetButton) {
  resetButton.addEventListener("click", async () => {
    stopSpeaking();

    clearSpeechBuffer();

    try {
      await fetch(`${SERVER}/reset`, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({}),

        cache: "no-store",
      });
    } catch (e) {
      console.warn("Reset failed:", e);
    }

    if (chatLog) {
      chatLog.innerHTML = "";
    }

    addMsg("jarvis", "Conversation cleared.");

    setState(
      activated ? "ready" : "sleeping",
      activated ? "MEMORY CLEARED" : "STANDBY",
    );
  });
}

// ============================================================
// MEMORY
// ============================================================

async function refreshMemory() {
  if (!memList) {
    return;
  }

  try {
    const response = await fetch(`${SERVER}/memory`, {
      signal: AbortSignal.timeout(3000),

      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    if (data.memory && data.memory.length) {
      memList.innerHTML = data.memory
        .map(
          (item, index) => `
              <div style="
                padding:2px 0;
                border-bottom:
                1px solid
                rgba(0,234,255,0.06)
              ">
                ${index + 1}.
                ${escapeHtml(item)}
              </div>
            `,
        )
        .join("");
    } else {
      memList.textContent = "Empty";
    }
  } catch (error) {
    memList.textContent = "Empty";
  }
}

refreshMemory();

setInterval(refreshMemory, 8000);

// ============================================================
// TIMERS & REMINDERS
// ============================================================

async function pollTimerNotifications() {
  try {
    const response = await fetch(`${SERVER}/timers/due`, {
      signal: AbortSignal.timeout(3000),

      cache: "no-store",
    });

    if (!response.ok) {
      return;
    }

    const data = await response.json();

    if (!data.ok || !Array.isArray(data.due)) {
      return;
    }

    for (const item of data.due) {
      const eventKey = `${item.id}:${
        item.last_triggered_at || item.updated_at || ""
      }`;

      if (spokenTimerEvents.has(eventKey)) {
        continue;
      }

      spokenTimerEvents.set(eventKey, Date.now());

      if (spokenTimerEvents.size > 200) {
        const oldest = spokenTimerEvents.keys().next().value;

        spokenTimerEvents.delete(oldest);
      }

      const kind = item.type === "timer" ? "timer" : "reminder";

      const title = removeSilentMetadata(item.title || "Reminder");

      const message =
        kind === "timer"
          ? "Sir, your timer has finished."
          : `Sir, reminder: ${title}.`;

      addMsg("jarvis", escapeHtml(message));

      if (isSpeaking) {
        speakQueue.push(cleanForSpeech(message));
      } else {
        speak(message);
      }
    }
  } catch (error) {
    console.debug("Timer polling:", error.message);
  }
}

pollTimerNotifications();

setInterval(pollTimerNotifications, 2000);

// ============================================================
// BOOT
// ============================================================

setTimeout(() => {
  const boot = removeSilentMetadata(randomLine("boot"));

  addMsg("jarvis", escapeHtml(boot));

  setState("sleeping", "INITIALIZING...");

  setTimeout(() => {
    speak(boot);
  }, 300);

  setTimeout(() => {
    setState(
      activated ? "ready" : "sleeping",
      activated ? "LISTENING" : "STANDBY",
    );
  }, 2200);
}, 800);
