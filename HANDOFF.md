# HANDOFF — Saathi (সাথী) · Build with Gemma: Kolkata hackathon

> Read this top-to-bottom to resume in a fresh chat. It captures **what the project
> is, every decision made, what's done, what's in progress, and what's left.**

---

## 0. TL;DR for the next session

- **Project:** *Saathi* — a **Bengali-first assistant** that reads a photographed
  government document with **Gemma (vision)**, explains it in simple Bengali, retrieves
  matching welfare schemes via **RAG**, and uses **function-calling tools** to check
  eligibility / set reminders / pre-fill forms.
- **Backend pipeline is FULLY WORKING and VERIFIED end-to-end** (vision + RAG +
  function-calling + Bengali answer) against real images. Runs on the laptop via Ollama.
- **Code is on GitHub (public):** https://github.com/Subharjun/saathi
- **TWO active tracks right now** (see §1a — this is the most important thing to understand):
  - **`main` branch** = the WORKING demo: laptop runs Gemma via Ollama; phone reaches it
    over a **cloudflared tunnel**; an **APK** was built via EAS pointing at that tunnel.
    This works today.
  - **`ondevice` branch** = an IN-PROGRESS rewrite to run **Gemma entirely on the phone**
    (no laptop, no server) using **llama.rn**. **Barely started — no code written yet.**
- **Immediate next step:** decide which track to finish. If continuing on-device, resume
  §7 (on-device build plan). If shipping the safe demo, use `main` + record the demo.
- **Deadline: 5 July 2026, 2:00 PM IST.** (Today in the last session was 4 July 2026.)

---

## 1. Key decisions (so we don't re-litigate them)

1. **Idea = Saathi** (document + scheme navigator for West Bengal). Exercises **4 Gemma
   capabilities at once** (vision, RAG, function-calling, on-device) → maxes the 30-pt
   "Gemma Integration" rubric item, strong India/Kolkata impact story.
2. **Runtime = LOCAL Gemma, NO API keys.** User cannot/does not want to manage API keys.
   This constraint has driven every hosting decision below.
3. **Model = `gemma3`** (Ollama tag) as a stand-in for "Gemma 4". Single env var
   `GEMMA_MODEL`. Gemma 3 is the latest open Gemma with **vision**, which we need.
4. **"Offline" positioning = offline-first, sync-when-online.** Honest framing.
5. **Solo build**, scope kept tight: one killer flow, editable demo profile.

### 1a. Hosting decisions made THIS session (critical context)

6. **Render was REJECTED.** The backend's `gemma.py` calls local Ollama for **BOTH**
   chat/vision **and** embeddings (`localhost:11434` `/api/chat` + `/api/embeddings`).
   Hosting on Render would need to run gemma3 (~3.3 GB, needs ~6-8 GB RAM) *and*
   nomic-embed — i.e. Render **Pro Plus ~$85/mo** with painfully slow CPU inference, OR
   swapping to a cloud API (**needs a key** the user doesn't have). Both were rejected.
7. **Chosen public path = cloudflared tunnel + EAS APK.** A `cloudflared` quick tunnel
   gives a public HTTPS URL that forwards to the laptop's Gemma. No key, free, fast
   (Mac GPU). The **APK** (built via EAS) points at that tunnel URL, so it works off-LAN.
   Trade-off: the **laptop + Ollama + backend + tunnel must all be running** during use.
   ⚠️ The `trycloudflare.com` URL is **EPHEMERAL** — restarting the tunnel mints a new URL,
   which requires editing `mobile/config.js` and **rebuilding the APK**.
8. **NEW DIRECTION (user's explicit call, against the recommendation): "go all-in
   phone-only"** — run Gemma fully on-device so no laptop/server is needed at all. This is
   the `ondevice` branch. It is a **large rebuild** and was **just started** (research done,
   no implementation yet). Risk was flagged: may not be demo-ready by the deadline, and
   **on-device inference cannot be tested from Claude** — it only runs on a physical phone.

---

## 2. Architecture

### Current working architecture (`main` branch)
```
Expo APK (phone)              internet (cloudflared tunnel)        FastAPI backend (laptop)
  camera + editable profile ──────────────────────────────►         POST /analyze
  Bengali answer + actions  ◄──────────────────────────────         Ollama: Gemma 3 (vision+chat)
                                                                     local RAG (nomic-embed)
                                                                     function-calling tools
```

### Target on-device architecture (`ondevice` branch, WIP)
```
Expo APK (phone) — everything runs on the device, no server:
  llama.rn (llama.cpp) running a Gemma 3 GGUF (+ mmproj for vision)
  lexical RAG over bundled schemes.json (no embed model)
  JS tools + JSON-based function calling
  (model GGUF downloaded from HuggingFace on first launch, then fully offline)
```

**Pipeline inside `POST /analyze` (backend) — same logic will port to on-device:**
1. **Vision** — Gemma reads the document image → JSON: `doc_type`, `summary_bn`,
   `key_points_bn`, `keywords_en`, `any_deadline`.
2. **RAG** — retrieve top-k of the 7 schemes in `backend/data/schemes.json`.
3. **Function calling** — Gemma emits a JSON plan of tool calls (see §3 fix), tools run
   deterministically: `check_eligibility`, `set_reminder`, `prefill_form`.
4. **Final answer** — tool results fed back → warm Bengali reply (`answer_bn`).

---

## 3. What's DONE ✅ (this session's work)

- **`gemma3` model finished downloading** — `ollama list` shows `gemma3:latest` (3.3 GB)
  and `nomic-embed-text:latest`.
- **BUG FOUND + FIXED: gemma3 has no native Ollama `tools` API.** Passing `tools=` to
  `/api/chat` returned `400: "gemma3:latest does not support tools"`, which made every
  `/analyze` call 500. **Fix:** switched to **prompt-based function calling** — Gemma emits
  a JSON plan `{"tool_calls":[{"name","arguments"}]}` via `format=json` (which works),
  tools run deterministically, results feed back into a grounded Bengali answer. Also
  hardened `run_tool` to drop unknown args. (Commit on `main`.)
- **Full pipeline VERIFIED end-to-end:**
  - Text path: RAG → `check_eligibility` → Bengali answer ✅
  - **Vision path**: tested against `~/Downloads/reimbursement.png` (a hospital bill) →
    Gemma read it ("Hospital Statement", Bengali summary, keywords, deadline) → RAG found
    স্বাস্থ্য সাথী / আয়ুষ্মান ভারত → `prefill_form` → warm Bengali answer ✅
  - All 4 Gemma capabilities confirmed working.
- **Test helper added:** `backend/test_analyze.py`
  - `./.venv/bin/python test_analyze.py` (text-only)
  - `./.venv/bin/python test_analyze.py <image.jpg> "<question>"` (with vision)
- **Git repo initialized + pushed PUBLIC:** https://github.com/Subharjun/saathi
  - Removed a stray nested `.git` inside `mobile/` (was the Expo scaffold's repo — would
    have made `mobile/` an empty submodule pointer in the public repo).
  - Root `.gitignore` excludes `.venv`, `node_modules`, `__pycache__`, `reminders.json`.
- **cloudflared tunnel** brought up and verified public (`/health` + POST `/analyze` work
  through it). NOTE: local Jio DNS returned NXDOMAIN briefly; resolving via 1.1.1.1 worked
  — phones resolve trycloudflare fine.
- **APK BUILT successfully on EAS** (on `main`): build id `98007499-21a3-4def-aef2-3fec58da3c10`,
  status **FINISHED**, profile `preview` (APK), EAS project `@subharjun/mobile`
  (projectId `3a3a2840-e963-40f4-b8fe-34c14ee9493c`).
  - **Download APK:** https://expo.dev/artifacts/eas/Yu6kYF4ZzHWCbhPDmmg3JmClethVECwz3zZkiCp6vjg.apk
  - Build page: https://expo.dev/accounts/subharjun/projects/mobile/builds/98007499-21a3-4def-aef2-3fec58da3c10
  - ⚠️ This APK is baked to the EPHEMERAL tunnel URL (`quarterly-harrison-heavy-jewel.trycloudflare.com`).
    If the tunnel restarted, the URL changed → update `mobile/config.js` and rebuild.

## 4. IN PROGRESS ⏳ — on-device rewrite (`ondevice` branch)

**Status: research done, NO code written yet. `ondevice` == `main` right now.**

Decided stack (from web research, confirmed current as of this session):
- **`llama.rn`** (v0.12.5, React Native binding of llama.cpp) — runs Gemma GGUF on-device,
  **supports multimodal vision** on Android. MIT. npm: `llama.rn`.
- **Model:** a **Gemma 3 4B GGUF** (Q4) + its **mmproj** file for vision. (Gemma 3n E2B/E4B
  are the mobile-optimized multimodal option — 2-3 GB RAM — but llama.cpp support for the
  3n architecture is less certain; 4B is the safer llama.cpp path. STILL NEED TO CONFIRM
  exact HuggingFace filenames — was fetching `ggml-org/gemma-3-4b-it-GGUF/tree/main` when
  the session ended.)
- **RAG:** replace embeddings with **lexical keyword matching in JS** over the 7 schemes
  (only 7 docs — no embed model needed; removes a big dependency).
- **Tools + function-calling:** port `check_eligibility`/`set_reminder`/`prefill_form` and
  the JSON-plan approach to JS.
- **Model delivery:** a ~3 GB GGUF **cannot be bundled in the APK** → download from
  HuggingFace on **first launch** (needs internet once, then fully offline). Store via
  `expo-file-system`.
- **Build:** llama.rn is a native module → **cannot run in Expo Go**. Needs an EAS
  **dev client / preview** build with the `llama.rn` config plugin + `expo-build-properties`.

llama.rn API reference (verbatim, for the implementation):
```js
import { initLlama } from 'llama.rn'
const ctx = await initLlama({ model:'file://<gguf>', n_ctx:2048, n_gpu_layers:99, ctx_shift:false /* required for multimodal */ })
await ctx.initMultimodal({ path:'<mmproj.gguf>', use_gpu:true })
const support = await ctx.getMultimodalSupport()   // {vision:true}
const r = await ctx.completion({ messages:[{role:'user', content:[
  {type:'text', text:'...'},
  {type:'image_url', image_url:{ url:'file:///path.jpg' /* or data:image/jpeg;base64,... */ }},
]}], n_predict:256, temperature:0.1 })
// r.text is the output. ctx.completion also supports plain {messages:[{role,content:'str'}]}.
```
app.json plugin block:
```js
plugins: [['llama.rn', { forceCxx20:true, enableOpenCL:true }]]
// plus expo-build-properties for iOS/OpenCL if needed
```

## 5. REMAINING / TODO 📋

**If finishing the on-device track (`ondevice` branch)** — resume this ordered plan:
1. Confirm exact Gemma GGUF + mmproj HuggingFace URLs (`ggml-org/gemma-3-4b-it-GGUF`).
2. `cd mobile`; add deps: `npx expo install llama.rn expo-build-properties expo-file-system`.
   Add the `llama.rn` config plugin to `app.json`.
3. Copy `backend/data/schemes.json` into the app and `import` it (bundle it).
4. Write `mobile/llm.js` — download model (with progress), `initLlama` + `initMultimodal`,
   `chat()`, `vision()`.
5. Write `mobile/rag.js` — lexical retrieval over schemes.
6. Write `mobile/tools.js` — the 3 tools + JSON function-calling runner.
7. Rewrite `mobile/App.js` — full on-device pipeline + a first-launch model-download screen.
   (Remove the `fetch(BACKEND_URL)` calls.)
8. `npx eas-cli build -p android --profile preview` → install APK on a real Android phone.
9. **User must test on a physical phone; Claude cannot test on-device inference.** Iterate.
   Watch for: device RAM (4B model needs a strong phone), model-download UX, vision support.

**If shipping the safe demo (`main` branch):**
1. Keep `ollama serve` + backend + cloudflared tunnel running; install the EAS APK.
2. Record a screen recording of the phone flow (safest demo artifact).

**Submission deliverables (required to be eligible):**
- **Kaggle Writeup** (≤1500 words) — user said "skip for now" last session; still TODO.
- **Public code repo** — ✅ DONE: https://github.com/Subharjun/saathi
- **Live demo** — screen recording of the phone flow.
- **Pitch/deck** — 3-4 slides: problem → demo → how Gemma powers it → impact.

---

## 6. Exact commands (current working `main` setup)

```bash
# --- Ollama (own terminal) ---
ollama serve
ollama list                       # gemma3:latest, nomic-embed-text:latest

# --- Backend ---
cd /Users/subharjunbose/Desktop/Kaggle-hackathon/backend
./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
curl -X POST http://localhost:8000/warmup      # build scheme embeddings
curl -s http://localhost:8000/health           # {"ok":true,"model":"gemma3","schemes":7}

# --- Public tunnel (for the APK) ---
cloudflared tunnel --url http://localhost:8000 # prints an EPHEMERAL https://<x>.trycloudflare.com
# → put that URL in mobile/config.js BACKEND_URL, then rebuild the APK

# --- Test the pipeline locally ---
cd backend && ./.venv/bin/python test_analyze.py ~/Downloads/reimbursement.png "এই কাগজে কী লেখা আছে?"

# --- Expo Go (same-WiFi dev, uses LAN IP not tunnel) ---
cd mobile && npx expo start

# --- Rebuild the APK ---
cd mobile && npx eas-cli build -p android --profile preview
```

---

## 7. Environment facts / gotchas

- **OS:** macOS (darwin 25.5), Apple Silicon. Dir: `/Users/subharjunbose/Desktop/Kaggle-hackathon`.
- **Mac LAN IP:** `192.168.31.120` (`ipconfig getifaddr en0`). For Expo Go, `config.js`
  can use `http://192.168.31.120:8000`; for the APK use the tunnel URL.
- **gemma3 has NO native Ollama tools API** — we use prompt-based JSON function calling.
  Do NOT re-introduce `tools=` in `gemma.chat()`.
- **Both chat AND embeddings** go through local Ollama — any "move backend to cloud" plan
  must replace BOTH models.
- **cloudflared tunnel URL is ephemeral** — new URL on every restart → update config + rebuild.
- **Python 3.14** — only prebuilt wheels (`--only-binary=:all:`). Deps in `backend/.venv`.
- **Node 25 / npm 11**, Expo SDK **57**, EAS logged in as `subharjun`
  (`subharjun.bose12@gmail.com`). No local Android SDK → APKs build on EAS cloud.
- **GitHub:** account `Subharjun`, repo `saathi` (public), remote `origin` on both branches.
- **`cloudflared` and `ngrok` are both installed** (`/opt/homebrew/bin`).
- **On-device caveat:** llama.rn needs a dev/preview build (not Expo Go); Claude cannot run
  on-device inference — testing requires the user's physical Android phone.
- `mobile/AGENTS.md` says: read https://docs.expo.dev/versions/v57.0.0/ before writing RN code.
- Backend must bind `--host 0.0.0.0`. Reminders write to `backend/data/reminders.json`.

---

## 8. Rubric mapping

| Rubric item (weight) | How Saathi earns it |
|---|---|
| Gemma Integration (30) | Vision + RAG + function-calling + on-device — Gemma is the whole pipeline |
| Innovation & Impact (30) | Bengali inclusion + welfare access; real Kolkata/India problem |
| Functionality (20) | Live phone demo; deterministic eligibility so it's convincing |
| Presentation (20) | "Bengali-speaking guide in your pocket"; README + this doc |

**Tracks:** Local Language & Inclusion (primary) or GenAI for Good.
**Deadline:** 5 July 2026, 2:00 PM IST. One submission per team (Kaggle Writeup).

---

## 9. File map

```
Kaggle-hackathon/                 (git: branches `main` [working] and `ondevice` [WIP])
├── HANDOFF.md            <- this file
├── README.md             <- judge-facing overview + run + demo script
├── .gitignore
├── backend/
│   ├── main.py           <- FastAPI + pipeline (prompt-based function calling)
│   ├── gemma.py          <- local Ollama client (chat/vision/embed)
│   ├── rag.py            <- offline cosine retrieval
│   ├── tools.py          <- function-calling tools (run_tool hardened)
│   ├── test_analyze.py   <- local pipeline tester (text or +image)
│   ├── data/schemes.json <- 7 real schemes (knowledge base)
│   ├── requirements.txt
│   └── .venv/
└── mobile/               <- Expo app (SDK 57), EAS project @subharjun/mobile
    ├── App.js            <- full UI + /analyze call (to be rewritten for on-device)
    ├── config.js         <- BACKEND_URL (currently the cloudflared tunnel URL)
    ├── app.json          <- has android.package=com.subharjun.saathi + EAS projectId
    ├── eas.json          <- preview profile builds an APK
    └── node_modules/
```

---

## 10. Git branch state (IMPORTANT)

- **`main`** — the working laptop+tunnel demo. All this session's backend fixes, the test
  script, git setup, and APK/tunnel config are committed and pushed here. **This is your
  safe fallback — it works.**
- **`ondevice`** — created from `main` for the phone-only rewrite. **No commits yet** beyond
  what `main` has (implementation not started). Currently checked out.
- To return to the safe demo: `git checkout main`.
- To continue the on-device build: `git checkout ondevice` and resume §5 / §4.
