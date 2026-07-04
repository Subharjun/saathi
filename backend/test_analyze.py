"""Quick local tester for the Saathi /analyze endpoint.

Usage:
  # text-only (no image) — tests RAG + tools + Bengali answer
  ./.venv/bin/python test_analyze.py

  # with a document photo — also tests the Gemma vision step
  ./.venv/bin/python test_analyze.py /path/to/document.jpg

  # with your own question
  ./.venv/bin/python test_analyze.py /path/to/doc.jpg "আমার কি এই টাকা পাওয়ার যোগ্যতা আছে?"
"""
import base64
import json
import sys

import requests

URL = "http://localhost:8000/analyze"

# Editable demo profile (matches the app's default profile).
PROFILE = {
    "name": "Mamata",
    "age": 34,
    "gender": "female",
    "state": "West Bengal",
    "occupation": "homemaker",
    "documents": ["aadhaar", "voter_id"],
}


def main():
    img_path = sys.argv[1] if len(sys.argv) > 1 else None
    question = sys.argv[2] if len(sys.argv) > 2 else "আমি কি সরকারি সাহায্য পেতে পারি?"

    payload = {"question": question, "profile": PROFILE}
    if img_path:
        with open(img_path, "rb") as f:
            payload["image_b64"] = base64.b64encode(f.read()).decode()
        print(f"[testing WITH image: {img_path}]")
    else:
        print("[testing text-only — pass an image path to also test vision]")

    print(f"[question: {question}]\n")
    r = requests.post(URL, json=payload, timeout=300)
    r.raise_for_status()
    d = r.json()

    doc = d.get("document") or {}
    if doc:
        print("=== VISION (Gemma read the document) ===")
        print("doc_type   :", doc.get("doc_type"))
        print("summary_bn :", doc.get("summary_bn"))
        print("keywords   :", doc.get("keywords_en"))
        print("deadline   :", doc.get("any_deadline"))
        print()

    print("=== RAG (retrieved schemes) ===")
    for s in d.get("retrieved_schemes", []):
        print(f"  {s['id']:<18} {round(s['score'], 3)}  {s['name']}")
    print()

    print("=== ACTIONS (tools Gemma chose to run) ===")
    for a in d.get("actions", []):
        res = a["result"]
        brief = f"eligible={res.get('eligible')}" if "eligible" in res else list(res.keys())
        print(f"  {a['tool']}({a['args']}) -> {brief}")
    print()

    print("=== ANSWER (Bengali) ===")
    print(d.get("answer_bn", ""))


if __name__ == "__main__":
    main()
