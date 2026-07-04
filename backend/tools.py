"""Callable tools exposed to Gemma via native function calling.

Gemma 4 decides *which* of these to invoke and with *what* arguments; we execute
them deterministically so eligibility is trustworthy (not hallucinated) and actions
(reminders, pre-filled forms) are real artifacts the user can act on.
"""
import json
import os
import time

from rag import index

REMINDERS = os.path.join(os.path.dirname(__file__), "data", "reminders.json")

# --- JSON schema advertised to Gemma -----------------------------------------
TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "check_eligibility",
            "description": "Check whether the user qualifies for a specific government scheme, given their profile.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scheme_id": {"type": "string", "description": "id of the scheme, e.g. lakshmir_bhandar"},
                },
                "required": ["scheme_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Set a reminder for a deadline, camp date, or document the user must arrange.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "when": {"type": "string", "description": "human-readable date/time, e.g. '15 August'"},
                },
                "required": ["title", "when"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "prefill_form",
            "description": "Produce a pre-filled application checklist for a scheme using the user's profile.",
            "parameters": {
                "type": "object",
                "properties": {"scheme_id": {"type": "string"}},
                "required": ["scheme_id"],
            },
        },
    },
]


# --- Implementations ----------------------------------------------------------
def check_eligibility(profile, scheme_id):
    s = index.by_id(scheme_id)
    if not s:
        return {"scheme_id": scheme_id, "eligible": None, "reason": "Unknown scheme."}
    rules = s.get("eligibility", {})
    reasons, eligible = [], True

    def fail(msg):
        nonlocal eligible
        eligible = False
        reasons.append(msg)

    age = profile.get("age")
    if "age_min" in rules and age is not None and age < rules["age_min"]:
        fail(f"age {age} is below minimum {rules['age_min']}")
    if "age_max" in rules and age is not None and age > rules["age_max"]:
        fail(f"age {age} is above maximum {rules['age_max']}")
    if rules.get("gender") and profile.get("gender") and profile["gender"] != rules["gender"]:
        fail(f"scheme is for {rules['gender']}")
    if rules.get("residence") == "west_bengal" and profile.get("state", "").lower() not in ("west bengal", "wb", ""):
        fail("scheme is for West Bengal residents")
    if rules.get("occupation") and profile.get("occupation") and profile["occupation"] != rules["occupation"]:
        fail(f"scheme is for {rules['occupation']}s")

    return {
        "scheme_id": scheme_id,
        "scheme_name": s["name_en"],
        "eligible": eligible,
        "reasons": reasons or ["meets the basic criteria"],
        "benefit_bn": s["benefit_bn"],
        "documents": s["documents"],
        "how_to_apply": s["how_to_apply"],
        "official_link": s["official_link"],
    }


def set_reminder(profile, title, when):
    rec = {"title": title, "when": when, "created": time.strftime("%Y-%m-%d %H:%M")}
    data = []
    if os.path.exists(REMINDERS):
        with open(REMINDERS, encoding="utf-8") as f:
            data = json.load(f)
    data.append(rec)
    with open(REMINDERS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"status": "reminder_set", **rec}


def prefill_form(profile, scheme_id):
    s = index.by_id(scheme_id)
    if not s:
        return {"error": "unknown scheme"}
    have = {d: (d.lower() in " ".join(profile.get("documents", [])).lower()) for d in s["documents"]}
    return {
        "scheme_id": scheme_id,
        "scheme_name": s["name_en"],
        "applicant": {k: profile.get(k) for k in ("name", "age", "gender", "state", "occupation")},
        "documents_status": have,
        "missing_documents": [d for d, ok in have.items() if not ok],
        "how_to_apply": s["how_to_apply"],
    }


REGISTRY = {
    "check_eligibility": check_eligibility,
    "set_reminder": set_reminder,
    "prefill_form": prefill_form,
}


def run_tool(name, args, profile):
    fn = REGISTRY.get(name)
    if not fn:
        return {"error": f"unknown tool {name}"}
    return fn(profile, **args)
