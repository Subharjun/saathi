# HANDOFF — Saathi (সাথী) · Build with Gemma: Kolkata hackathon

> Read this top-to-bottom to resume in a fresh chat. It captures **what the project
> is, every decision made, what's done, what's in progress, and what's left.**

---

## 0. TL;DR for the next session

- **Project:** *Saathi* — an **offline, Bengali-first assistant** that reads a photographed
  government document with **Gemma (vision)**, explains it in simple Bengali, retrieves
  matching welfare schemes via **RAG**, and uses **function-calling tools** to check
  eligibility / set reminders / pre-fill forms.
- **Stack:** FastAPI backend on the laptop + **local Ollama** running Gemma (no cloud,
  **no API keys**) + **React Native (Expo)** phone app talking to the laptop over LAN.
- **Where we are:** All code written and backend boots healthy. **`gemma3` model was
  ~50% downloaded** when this handoff was written; `nomic-embed-text` is done. The only
  thing blocking a full end-to-end test is the `gemma3` download finishing.
- **Immediate next step:** confirm `ollama list` shows `gemma3`, run the warmup +
  a real `/analyze` call, then run the Expo app on a phone.

---

## 1. Key decisions (so we don't re-litigate them)

1. **Idea = Saathi** (document + scheme navigator for West Bengal). Chosen because it
   naturally exercises **4 Gemma capabilities at once** (vision, RAG, function-calling,
   on-device) → maxes the 30-pt "Gemma Integration" rubric item, and tells a strong
   India/Kolkata impact story.
2. **Runtime = LOCAL Ollama, NO API keys.** User explicitly does not want to manage
   API keys. So we run Gemma on the laptop via Ollama; the phone reaches it over WiFi.
   (We briefly considered hosted Google AI Studio — **rejected** to avoid API keys.)
3. **Model = `gemma3` as a stand-in for "Gemma 4".** There is no pullable "gemma4" tag
   yet. The model name is a single env var (`GEMMA_MODEL`), so switching to a real
   `gemma4` later is a one-line change, no code edits. Gemma 3 is the latest open Gemma
   with **vision**, which we need.
4. **"Offline" positioning = offline-first, sync-when-online.** Honest framing for the
   writeup: inference + retrieval run offline for the last-mile user; the scheme
   knowledge base is refreshed when the device has internet. Do NOT claim "always
   current with zero internet" — a technical judge will call that out.
5. **Solo build**, so scope is kept tight: one killer flow, editable demo profile.

---

## 2. Architecture

```
Expo app (phone)                 LAN / hotspot, no internet         FastAPI backend (laptop)
  camera + editable profile   ───────────────────────────────►       POST /analyze
  Bengali answer + actions    ◄───────────────────────────────       Ollama: Gemma 3 (vision + chat)
                                                                      local RAG over scheme docs
                                                                      function-calling tools
```

**Pipeline inside `POST /analyze`:**
1. **Vision** — Gemma reads the document image → JSON: `doc_type`, `summary_bn`,
   `key_points_bn`, `keywords_en`, `any_deadline`.
2. **RAG** — embed the extracted text (nomic-embed-text) → cosine top-k over the
   7 schemes in `backend/data/schemes.json`.
3. **Function calling** — Gemma is given the doc + profile + candidate schemes + tool
   specs, and decides which tools to call: `check_eligibility`, `set_reminder`,
   `prefill_form`. Tools run deterministically (eligibility is NOT hallucinated).
4. **Final answer** — tool results fed back → warm Bengali reply (`answer_bn`).

---

## 3. What's DONE ✅

- **Backend fully coded and boots healthy** (`curl http://localhost:8000/health`
  → `{"ok":true,"model":"gemma3","schemes":7}`).
  - `backend/main.py` — FastAPI app + the 4-step pipeline (`/health`, `/warmup`, `/analyze`).
  - `backend/gemma.py` — local Ollama client: `chat()` (with image + tools support),
    `embed()`, `force_json()`. Model via `GEMMA_MODEL` env (default `gemma3`).
  - `backend/rag.py` — offline cosine-similarity retrieval over the schemes.
  - `backend/tools.py` — `check_eligibility`, `set_reminder`, `prefill_form` + JSON
    tool specs advertised to Gemma.
  - `backend/data/schemes.json` — 7 real schemes (Lakshmir Bhandar, Kanyashree,
    Swasthya Sathi, Krishak Bandhu, PM-JAY, PM-KISAN, Jai Bangla pension).
  - `backend/requirements.txt` — **relaxed pins** (numpy>=2.3.3 etc.) because Python
    3.14 has no wheels for older numpy/pydantic (they build from source → slow/fragile).
  - Deps installed in `backend/.venv` (numpy 2.5.0, pydantic 2.13.4). **Verified importing.**
- **Mobile app fully coded** and deps installed (`mobile/node_modules` present,
  incl. `expo-image-picker`).
  - `mobile/App.js` — camera/gallery capture (base64), editable demo profile, calls
    `/analyze`, renders doc summary + actions + Bengali answer. Dark themed, Bengali UI.
  - `mobile/config.js` — `BACKEND_URL` **already set to `http://192.168.31.120:8000`**
    (this Mac's current LAN IP).
- **`nomic-embed-text` model pulled.**
- **`README.md`** written (doubles as the judge-facing repo doc + demo script).

## 4. IN PROGRESS ⏳

- **`gemma3` model download** — was ~50% (1.7/3.3 GB) at handoff time. Resume check:
  `ollama list` (should show `gemma3`) and `tail -1 /tmp/pull_gemma.log`.
  If interrupted, just re-run `ollama pull gemma3`.

## 5. REMAINING / TODO 📋

1. **End-to-end test** once `gemma3` is present:
   - `curl -X POST http://localhost:8000/warmup` (builds embeddings for the 7 schemes).
   - Test `/analyze` with a document image (base64). No sample image exists yet — either
     photograph a real form, or generate one (Pillow install was declined earlier;
     re-ask user before adding it).
2. **Run the Expo app on a real phone** (`cd mobile && npx expo start`, scan QR in
   Expo Go, phone + laptop on same WiFi). Confirm the full loop works.
3. **(Optional, high-impact) Bengali TTS** — have the app speak `answer_bn` aloud using
   `expo-speech` (on-device, no key). Big accessibility win for non-readers. ~30 min.
4. **Submission deliverables (required to be eligible):**
   - **Kaggle Writeup** (<=1500 words): problem, architecture, how Gemma is used,
     challenges, why the choices. Use `README.md` + this file as source material.
   - **Public code repo** (GitHub). NOTE: project is **not a git repo yet** — need
     `git init`, add a root `.gitignore` (exclude `.venv`, `node_modules`, `__pycache__`),
     commit, push.
   - **Live demo** — a screen recording / terminal recording of the phone flow is the
     safest "demo" artifact for a local-model app (can't host a laptop-only backend).
5. **Pitch/deck** — 3-4 slides: problem → live demo → how Gemma powers it → impact.

---

## 6. Exact commands to run everything

```bash
# --- Ollama (keep running in its own terminal) ---
ollama serve
ollama list                       # confirm: gemma3, nomic-embed-text
# if gemma3 missing: ollama pull gemma3

# --- Backend ---
cd /Users/subharjunbose/Desktop/Kaggle-hackathon/backend
./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
# in another terminal, warm up RAG:
curl -X POST http://localhost:8000/warmup
curl -s http://localhost:8000/health

# --- Mobile ---
cd /Users/subharjunbose/Desktop/Kaggle-hackathon/mobile
npx expo start                    # scan QR with Expo Go app
```

Switch the model later (e.g. real gemma4):
```bash
GEMMA_MODEL=gemma4 ./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 7. Environment facts / gotchas

- **OS:** macOS (darwin 25.5), Apple Silicon. **Working dir:** `/Users/subharjunbose/Desktop/Kaggle-hackathon`.
- **Mac LAN IP:** `192.168.31.120` (from `ipconfig getifaddr en0`). If the network
  changes, update `mobile/config.js` `BACKEND_URL` and re-run.
- **Python 3.14** is installed and very new → **only use prebuilt wheels**
  (`pip install --only-binary=:all: ...`). Old numpy/pydantic pins build from source.
- **Node 25 / npm 11**, Expo SDK **57**, React **19**, RN **0.86**.
- **Ollama** 0.20.2 installed. `ollama serve` must be running for the backend to work.
- Backend must bind **`--host 0.0.0.0`** (not 127.0.0.1) so the phone can reach it.
- Reminders are written to `backend/data/reminders.json` (created on first `set_reminder`).

---

## 8. Rubric mapping (how each part scores)

| Rubric item (weight) | How Saathi earns it |
|---|---|
| Gemma Integration (30) | Vision + RAG + function-calling + on-device — Gemma is the whole pipeline |
| Innovation & Impact (30) | Bengali language inclusion + welfare access; real Kolkata/India problem |
| Functionality (20) | Live phone→laptop demo; deterministic eligibility so it's convincing |
| Presentation (20) | "Bengali-speaking guide in your pocket, offline"; README + this doc |

**Tracks it fits:** Local Language & Inclusion (primary) or GenAI for Good.
**Deadline:** 5 July 2026, 2:00 PM IST. One submission per team (Kaggle Writeup).

---

## 9. File map

```
Kaggle-hackathon/
├── HANDOFF.md            <- this file
├── README.md             <- judge-facing overview + run + demo script
├── backend/
│   ├── main.py           <- FastAPI + pipeline
│   ├── gemma.py          <- local Ollama client (chat/vision/embed)
│   ├── rag.py            <- offline cosine retrieval
│   ├── tools.py          <- function-calling tools
│   ├── data/schemes.json <- 7 real schemes (knowledge base)
│   ├── requirements.txt  <- relaxed pins for Python 3.14
│   └── .venv/            <- installed deps (numpy 2.5, pydantic 2.13, fastapi, uvicorn)
└── mobile/               <- Expo app
    ├── App.js            <- full UI + /analyze call
    ├── config.js         <- BACKEND_URL = http://192.168.31.120:8000
    └── node_modules/     <- installed (incl. expo-image-picker)
```
```
