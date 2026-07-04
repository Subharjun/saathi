"""Saathi backend — offline Gemma 4 pipeline: vision -> RAG -> function calling -> Bengali answer.

Run:  uvicorn main:app --host 0.0.0.0 --port 8000
The --host 0.0.0.0 is what lets the phone reach it over the LAN / hotspot.
"""
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import gemma
from rag import index
from tools import TOOL_SPECS, run_tool

app = FastAPI(title="Saathi")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class AnalyzeRequest(BaseModel):
    image_b64: str | None = None          # base64 of the photographed document
    question: str | None = None            # optional spoken/typed question, any language
    profile: dict = {}                     # {name, age, gender, state, occupation, documents:[...]}


VISION_PROMPT = (
    "You are Saathi, a helpful assistant for people in West Bengal, India. "
    "Look at this photo of an official document (form, notice, prescription, card, or letter). "
    "Return ONLY JSON with keys: "
    "doc_type (short English label), summary_bn (2-3 simple Bengali sentences a villager can understand), "
    "key_points_bn (array of short Bengali strings), keywords_en (array of English keywords for retrieval), "
    "any_deadline (English date string or null)."
)


@app.get("/health")
def health():
    return {"ok": True, "model": gemma.GEMMA_MODEL, "schemes": len(index.schemes)}


@app.post("/warmup")
def warmup():
    n = index.build()
    return {"embedded_schemes": n}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    # 1) VISION — Gemma reads the document into structured Bengali.
    doc = {}
    if req.image_b64:
        msg = gemma.chat(
            [{"role": "user", "content": VISION_PROMPT}],
            images=[req.image_b64],
            fmt="json",
        )
        doc = gemma.force_json(msg)

    # 2) RAG — retrieve schemes relevant to the document + question.
    query = " ".join(
        filter(None, [req.question, doc.get("doc_type", ""), " ".join(doc.get("keywords_en", []))])
    ) or (req.question or "government scheme help")
    retrieved = index.search(query, k=3)

    # 3) FUNCTION CALLING — Gemma decides which tools to run.
    context = {
        "document": doc,
        "user_profile": req.profile,
        "candidate_schemes": [
            {"id": s["id"], "name": s["name_en"], "benefit": s["benefit_en"], "eligibility": s["eligibility"]}
            for s in retrieved
        ],
        "user_question": req.question,
    }
    sys = (
        "You are Saathi. Help this West Bengal user understand their document and access government schemes. "
        "Use check_eligibility on the most relevant candidate scheme(s). If there is a deadline or a camp date, "
        "call set_reminder. If the user clearly wants to apply, call prefill_form. "
        "Then reply to the user in warm, simple BENGALI."
    )
    messages = [
        {"role": "system", "content": sys},
        {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
    ]
    first = gemma.chat(messages, tools=TOOL_SPECS)

    tool_results = []
    for call in first.get("tool_calls", []) or []:
        fn = call["function"]["name"]
        args = call["function"].get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        result = run_tool(fn, args, req.profile)
        tool_results.append({"tool": fn, "args": args, "result": result})

    # 4) FINAL ANSWER — feed tool results back for a grounded Bengali reply.
    if tool_results:
        messages.append(first)
        for tr in tool_results:
            messages.append(
                {"role": "tool", "content": json.dumps(tr["result"], ensure_ascii=False)}
            )
        final = gemma.chat(messages)
        answer_bn = final.get("content", "")
    else:
        answer_bn = first.get("content", "")

    return {
        "document": doc,
        "retrieved_schemes": [{"id": s["id"], "name": s["name_bn"], "score": s["score"]} for s in retrieved],
        "actions": tool_results,
        "answer_bn": answer_bn,
    }
