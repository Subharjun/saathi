# Saathi (সাথী) — your offline scheme & document companion

**Build with Gemma: Kolkata — Track: Local Language & Inclusion / GenAI for Good**

Millions in West Bengal miss out on government schemes and misread official
documents because the paperwork is in dense English or formal Bengali. **Saathi**
lets anyone photograph *any* official document — a form, a notice, a prescription,
a card — and get it explained in plain spoken Bengali, learn which schemes they
qualify for, and act on it. **It runs fully offline. No cloud. No internet.**

## How Gemma 4 is used (core to the solution)

Saathi chains **four** Gemma 4 capabilities in a single flow:

1. **Vision-to-text** — Gemma 4 reads the photographed document and extracts a
   structured Bengali summary, key points, and any deadline.
2. **RAG** — the extracted text retrieves the most relevant government schemes from
   a local, embedded knowledge base (embeddings also computed locally via Gemma-stack).
3. **Native function calling** — Gemma 4 decides which tools to invoke:
   `check_eligibility`, `set_reminder`, `prefill_form`. Eligibility is computed
   deterministically so it is trustworthy, not hallucinated.
4. **Offline / on-device inference** — everything runs on a local Ollama server.
   Kill the WiFi during the demo and it still works.

## Architecture

```
Expo app (phone)  --LAN / hotspot, no internet-->  FastAPI backend (laptop)
  camera + profile                                   Ollama: Gemma 4 (vision + tools)
  Bengali answer + actions                           local RAG over WB scheme docs
```

## Run it

### 1. Backend (laptop)
```bash
# one-time: install Ollama, then pull the models
ollama serve                         # keep running
ollama pull gemma3                   # use the gemma4 tag once available
ollama pull nomic-embed-text

cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
# warm up the RAG index:
curl -X POST http://localhost:8000/warmup
```

### 2. Mobile app (Expo)
```bash
cd mobile
npm install
# point the app at your laptop's LAN IP (see config.js)
npx expo start
```
Scan the QR with Expo Go on your phone (phone + laptop on the same WiFi / hotspot).

## Repo layout
- `backend/main.py` — the Gemma pipeline (vision → RAG → tools → answer)
- `backend/gemma.py` — local Ollama client (chat, vision, embeddings)
- `backend/rag.py` — offline cosine-similarity retrieval
- `backend/tools.py` — function-calling tools Gemma can invoke
- `backend/data/schemes.json` — grounded knowledge base of real WB/central schemes
- `mobile/` — Expo React Native app

## Demo script (90s)
1. Show phone in **airplane mode** (only laptop hotspot on) — "no internet."
2. Photograph a Lakshmir Bhandar / Swasthya Sathi form.
3. Saathi speaks the Bengali summary, flags the deadline, checks eligibility,
   sets a reminder, and lists the exact documents to bring.
