// ============================================================
// J.A.R.V.I.S. — app.js
// BATCH 1 — STABLE JSON EDITION
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

let cmdTimer = null;
let finalBuffer = "";

let isSpeaking = false;
let jarvisVoice = null;

let activeRequest = null;

// ============================================================
// VOICE
// ============================================================

const LANG = "en-US";

const WAKE_RE =
  /\b(?:(?:hey|ok|okay)\s+)?(?:jarvis|jarvas|jervis|jarvi|gervais|travis|charvis|jarvus)\b/gi;

const SLEEP_RE =
  /\b(?:go offline|go to sleep|sleep mode|go sleep|jarvis sleep|stand by|standby|good night)\b/i;

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
// TEXT CLEANUP
// ============================================================

function jarvisize(text) {
  const clean = String(text || "").trim();

  if (!clean) {
    return "Nothing to report.";
  }

  return clean;
}

// ============================================================
// COMMAND NORMALIZATION
// ============================================================

function normalizeCommand(text) {
  let c = String(text || "")
    .toLowerCase()
    .trim();

  c = c.replace(/[.,!?;:]+/g, " ");

  c = c.replace(/\s+/g, " ").trim();

  const replacements = [
    [/\bnot\s+pad\b/g, "notepad"],
    [/\bnote\s+pad\b/g, "notepad"],
    [/\bnote-pad\b/g, "notepad"],
    [/\bnotepadd\b/g, "notepad"],

    [/\bcrhome\b/g, "chrome"],
    [/\bchrom\b/g, "chrome"],

    [/\byou\s*tube\b/g, "youtube"],
    [/\byou\s*tub\b/g, "youtube"],

    [/\bspot\s*ify\b/g, "spotify"],
    [/\bspotty\s*fy\b/g, "spotify"],

    [/\bdis\s*cord\b/g, "discord"],

    [/\bcalc\b/g, "calculator"],

    [/\btask\s*man\b/g, "task manager"],

    [/\bvs\s*code\b/g, "vscode"],

    [/\bpower\s*shell\b/g, "powershell"],

    [/\bfile\s*explorer\b/g, "file explorer"],
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
    });

    if (!response.ok) {
      throw new Error("Health request failed");
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
    console.warn("Health check failed:", err.message);
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
  const div = document.createElement("div");

  div.className = `msg ${role}`;

  div.innerHTML = `<div class="lbl">
      ${role === "user" ? "YOU" : "JARVIS"}
    </div>
    <div class="txt">${html}</div>`;

  const shouldScroll = isNearBottom();

  chatLog.appendChild(div);

  if (shouldScroll) {
    scrollToLatest();
  }

  return div;
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
  if (!text) {
    return;
  }

  speakQueue.push(text);

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

    setState(
      activated ? "ready" : "sleeping",
      activated ? "LISTENING" : "STANDBY",
    );

    setTimeout(tryStartRecognition, 300);

    return;
  }

  queueRunning = true;
  isSpeaking = true;

  abortRecognition();

  if (stopBtn) {
    stopBtn.style.display = "flex";
  }

  const text = speakQueue.shift();

  const utterance = new SpeechSynthesisUtterance(text);

  utterance.rate = 1.02;
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
  if (!window.speechSynthesis) {
    setState("ready", "LISTENING");

    return;
  }

  speakQueue.length = 0;

  speechSynthesis.cancel();

  setState("speaking", "RESPONDING...");

  speakQueued(text);
}

// ============================================================
// STOP
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

  setState(
    activated ? "ready" : "sleeping",
    activated ? "LISTENING" : "STANDBY",
  );

  setTimeout(tryStartRecognition, 250);
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
// SEND MESSAGE
// ============================================================

async function sendMessage(text) {
  text = normalizeCommand(text);

  if (!text) {
    setState("ready", "LISTENING");

    return;
  }

  addMsg("user", escapeHtml(text));

  setState("thinking", randomLine("thinking").toUpperCase());

  const messageEl = addMsg(
    "jarvis",
    `<span class="typing">
        <span>.</span>
        <span>.</span>
        <span>.</span>
      </span>`,
  );

  const output = messageEl.querySelector(".txt");

  try {
    activeRequest = new AbortController();

    const response = await fetch(`${SERVER}/stream`, {
      method: "POST",

      headers: {
        "Content-Type": "text/plain;charset=UTF-8",
      },

      body: JSON.stringify({
        message: text,
      }),

      signal: activeRequest.signal,
    });

    activeRequest = null;

    if (!response.ok) {
      let serverMessage = `Server returned HTTP ${response.status}.`;

      try {
        const errorData = await response.json();

        if (errorData.reply) {
          serverMessage = errorData.reply;
        }

        if (errorData.error) {
          serverMessage = errorData.error;
        }
      } catch (e) {}

      output.textContent = serverMessage;

      speak(serverMessage);

      setState("ready", "LISTENING");

      return;
    }

    const data = await response.json();

    if (!data.ok) {
      const error =
        data.reply || data.error || "The server returned an error, Sir.";

      output.textContent = error;

      speak(error);

      setState("ready", "LISTENING");

      return;
    }

    const reply = jarvisize(data.reply);

    output.textContent = reply;

    speak(reply);

    refreshMemory();
  } catch (err) {
    activeRequest = null;

    console.error("JARVIS request failed:", err);

    let message;

    if (err.name === "AbortError") {
      message = "Request cancelled, Sir.";
    } else {
      message = "I couldn't reach the JARVIS server, Sir.";
    }

    output.textContent = "✕ " + message;

    speak(message);

    setState("ready", "LISTENING");
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
// RESTORED STABLE VERSION
// ============================================================

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;

let rec = null;

// ============================================================
// START RECOGNITION
// ============================================================

function tryStartRecognition() {
  if (!SR) {
    return;
  }

  if (isSpeaking) {
    return;
  }

  if (mode === "thinking") {
    return;
  }

  if (!rec) {
    return;
  }

  try {
    rec.start();

    console.log("Speech recognition started.");
  } catch (error) {
    console.debug("Speech recognition start:", error.message);
  }
}

// ============================================================
// ABORT RECOGNITION
// ============================================================

function abortRecognition() {
  if (!rec) {
    return;
  }

  try {
    rec.abort();
  } catch (error) {}
}

// ============================================================
// SLEEP
// ============================================================

function goSleep() {
  activated = false;

  finalBuffer = "";

  clearTimeout(cmdTimer);

  abortRecognition();

  speakQueue.length = 0;

  queueRunning = false;

  if (window.speechSynthesis) {
    speechSynthesis.cancel();
  }

  const goodbye = new SpeechSynthesisUtterance(randomLine("offline"));

  goodbye.rate = 1.02;
  goodbye.pitch = 0.84;
  goodbye.volume = 1;

  if (jarvisVoice) {
    goodbye.voice = jarvisVoice;
  }

  setState("speaking", "POWERING DOWN...");

  isSpeaking = true;

  if (stopBtn) {
    stopBtn.style.display = "flex";
  }

  const done = () => {
    isSpeaking = false;

    if (stopBtn) {
      stopBtn.style.display = "none";
    }

    setState("sleeping", "STANDBY");

    setTimeout(tryStartRecognition, 500);
  };

  goodbye.onend = done;
  goodbye.onerror = done;

  speechSynthesis.speak(goodbye);
}

// ============================================================
// SPEECH ENGINE
// ============================================================

if (SR) {
  rec = new SR();

  rec.continuous = true;
  rec.interimResults = true;
  rec.maxAlternatives = 5;
  rec.lang = LANG;

  // ----------------------------------------------------------
  // RESULT
  // ----------------------------------------------------------

  rec.onresult = (event) => {
    if (isSpeaking || mode === "thinking" || mode === "speaking") {
      return;
    }

    const result = event.results[event.results.length - 1];

    const alternatives = Array.from(result)
      .map((item) => item.transcript.toLowerCase().trim())
      .filter(Boolean);

    if (!alternatives.length) {
      return;
    }

    const best = alternatives[0];

    const wakeAlternative = alternatives.find((text) => {
      WAKE_RE.lastIndex = 0;

      return WAKE_RE.test(text);
    });

    // --------------------------------------------------------
    // SLEEPING
    // --------------------------------------------------------

    if (!activated) {
      if (!wakeAlternative) {
        return;
      }

      activated = true;
    }

    // --------------------------------------------------------
    // SLEEP COMMAND
    // --------------------------------------------------------

    if (activated && result.isFinal && SLEEP_RE.test(best)) {
      goSleep();

      return;
    }

    // --------------------------------------------------------
    // REMOVE WAKE WORD
    // --------------------------------------------------------

    const command = (wakeAlternative || best)
      .replace(WAKE_RE, " ")
      .replace(/\s+/g, " ")
      .trim();

    // --------------------------------------------------------
    // WAKE ONLY
    // --------------------------------------------------------

    if (!command) {
      clearTimeout(cmdTimer);

      if (mode === "sleeping") {
        cmdTimer = setTimeout(() => {
          abortRecognition();

          setState("ready", "LISTENING");

          speak(randomLine("wake"));
        }, 500);
      }

      return;
    }

    // --------------------------------------------------------
    // COMMAND
    // --------------------------------------------------------

    cmdInput.value = normalizeCommand(command);

    clearTimeout(cmdTimer);

    cmdTimer = setTimeout(
      () => {
        const finalCommand = normalizeCommand(command);

        cmdInput.value = "";

        abortRecognition();

        if (finalCommand) {
          sendMessage(finalCommand);
        }
      },
      result.isFinal ? 150 : 900,
    );
  };

  // ----------------------------------------------------------
  // ERROR
  // ----------------------------------------------------------

  rec.onerror = (event) => {
    console.warn("Speech recognition:", event.error);

    if (
      event.error === "not-allowed" ||
      event.error === "service-not-allowed"
    ) {
      wakeStatus.textContent = "MIC BLOCKED";

      wakeStatus.style.color = "#ff4400";

      return;
    }

    if (event.error === "network") {
      wakeStatus.textContent = "VOICE RETRY";

      wakeStatus.style.color = "#ffaa00";

      return;
    }

    if (event.error === "aborted") {
      return;
    }

    if (event.error === "no-speech") {
      return;
    }
  };

  // ----------------------------------------------------------
  // END
  // ----------------------------------------------------------

  rec.onend = () => {
    if (!isSpeaking && mode !== "thinking") {
      setTimeout(tryStartRecognition, 250);
    }
  };

  // ----------------------------------------------------------
  // MICROPHONE BUTTON
  // ----------------------------------------------------------

  if (micBtn) {
    micBtn.addEventListener("click", () => {
      activated = true;

      setState("ready", "LISTENING");

      tryStartRecognition();

      speak(randomLine("wake"));
    });
  }

  // ----------------------------------------------------------
  // INITIAL START
  // ----------------------------------------------------------

  setTimeout(tryStartRecognition, 1000);

  document.addEventListener(
    "click",
    () => {
      tryStartRecognition();
    },
    { once: true },
  );
} else {
  wakeStatus.textContent = "USE CHROME";

  wakeStatus.style.color = "#ff4400";
}

// ============================================================
// TYPED INPUT
// ============================================================

async function sendTyped() {
  const text = cmdInput.value.trim();

  if (!text) {
    return;
  }

  cmdInput.value = "";

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

    finalBuffer = "";

    try {
      await fetch(`${SERVER}/reset`, {
        method: "POST",

        headers: {
          "Content-Type": "text/plain;charset=UTF-8",
        },

        body: "{}",
      });
    } catch (e) {
      console.warn("Reset failed:", e);
    }

    chatLog.innerHTML = "";

    addMsg("jarvis", "Conversation cleared.");

    setState("ready", "MEMORY CLEARED");

    setTimeout(() => {
      setState(
        activated ? "ready" : "sleeping",
        activated ? "LISTENING" : "STANDBY",
      );
    }, 1500);
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
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    if (data.memory && data.memory.length) {
      memList.innerHTML = data.memory
        .map(
          (item, index) =>
            `<div style="
                padding:2px 0;
                border-bottom:
                1px solid
                rgba(0,234,255,0.06)
              ">
                ${index + 1}.
                ${escapeHtml(item)}
              </div>`,
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
// BOOT
// ============================================================

setTimeout(() => {
  const boot = randomLine("boot");

  addMsg("jarvis", boot);

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
