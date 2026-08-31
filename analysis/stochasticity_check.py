#!/usr/bin/env python3
"""
Preprint 2 stochasticity check · production-matched Gemini prompt.
Uses the new google-genai SDK (video_metadata supported).

Setup:
  pip3 install google-genai
  export GEMINI_API_KEY=your_key_here

Run:
  python3 stochasticity_check.py

Cost: ~$3-5 for N_RUNS=7 across 63 API calls (~30 minutes)
"""

import os
import json
import csv
import time
from collections import Counter

from google import genai
from google.genai import types

# ---------------------------------------------------------------
# Config
# ---------------------------------------------------------------
N_RUNS = 7
SLEEP_BETWEEN = 2
OUTPUT_CSV = "/tmp/stochasticity_results.csv"

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# ---------------------------------------------------------------
# The three hedged clips · exact values from production DB
# ---------------------------------------------------------------
CLIPS = [
    {
        "id": "3c75d0f2-54de-4129-97e4-34b66b38d135",
        "title": "Maverick Top Gun",
        "video_id": "lv6MclGClok",
        "start_seconds": 22,
        "end_seconds": 80,
        "target_person_description": None,
        "social_complexity": "moderate",
        "primary_spoken_language": "en",
    },
    {
        "id": "dda56bd7-fbf4-4bdc-a14c-59a808f0b174",
        "title": "Elemental Movie",
        "video_id": "e3hoiq_CPLs",
        "start_seconds": 0,
        "end_seconds": 25,
        "target_person_description": "Fire Girl",
        "social_complexity": "moderate",
        "primary_spoken_language": "en",
    },
    {
        "id": "9daf8586-5b67-4a4e-9926-4857cdc1117c",
        "title": "Demolition Movie CLIP",
        "video_id": "tXo52-_Zv04",
        "start_seconds": 0,
        "end_seconds": 57,
        "target_person_description": None,
        "social_complexity": "simple",
        "primary_spoken_language": "en",
    },
]

CONDITIONS = ["clean", "with_title", "legacy_full_metadata"]

# ---------------------------------------------------------------
# Exact production taxonomy
# ---------------------------------------------------------------
EMOTION_CODES = [
    "happy_amused", "proud", "moved", "affectionate", "surprised",
    "disappointed", "sad", "angry_frustrated", "contempt",
    "anxious_nervous", "scared", "embarrassed_awkward", "confused",
    "neutral", "mixed_more_than_one",
]
CUE_CODES = [
    "facial_expression", "tone_of_voice", "verbal_content", "body_language",
    "situation_context", "timing_pacing", "others_reaction",
    "something_else", "not_sure",
]

# ---------------------------------------------------------------
# Exact production SYSTEM_PROMPT
# ---------------------------------------------------------------
SYSTEM_PROMPT = f"""You are an emotion-reading research assistant for MindLens Lab. You watch a short video clip and provide ONE careful, hedged interpretation — knowing that real human readers will give many legitimate interpretations of the same moment.

Core principles:
1. You are ONE reader, not THE reader. Your output sits alongside plural human readings.
2. Hedge openly — "the eyebrows suggest...", "the tone hints at...".
3. Note what's ambiguous. If two readings are equally valid, say so.
4. NEVER claim certainty about the person's true internal state.
5. Acknowledge cultural / situational variation when it matters.

You will be told whose emotion to read (e.g., "the woman in the front"). Focus on that person; reference others only when their reactions inform your reading.

HARD LENGTH LIMITS (DB-enforced — exceeding will fail):
- candidate_rationale:       MAX 400 characters total. Aim for 2 short sentences.
- candidate_ambiguity_notes: MAX 200 characters total. One short sentence, or "".

Output format: return STRICT JSON, no markdown fences, no commentary outside JSON.
{{
  "candidate_primary_emotion": <one emotion code>,
  "candidate_secondary_emotions": [<0-3 emotion codes>],
  "candidate_cues": [<1-4 cue codes>],
  "candidate_rationale": "<≤400 chars, 2 short sentences referencing what you observed in the clip — facial expression, tone, body language, situation, etc.>",
  "candidate_ambiguity_notes": "<≤200 chars, 1 short sentence on other reasonable readings, or empty string>"
}}

Allowed emotion codes: {", ".join(EMOTION_CODES)}
Allowed cue codes: {", ".join(CUE_CODES)}"""


def build_user_prompt(clip, condition):
    lines = [
        "Clip context (curator notes — the actual clip is attached above):",
    ]
    if clip["target_person_description"]:
        lines.append(f'- Whose emotion to read: "{clip["target_person_description"]}"')
    else:
        lines.append("- Whose emotion to read: the primary person on screen (no specific framing)")

    if condition in ("with_title", "legacy_full_metadata"):
        lines.append(f'- Title (internal): {clip["title"]}')
    if condition == "legacy_full_metadata":
        lines.append(f'- Social complexity (curator-assigned): {clip["social_complexity"]}')
        if clip["primary_spoken_language"]:
            lines.append(f'- Primary spoken language: {clip["primary_spoken_language"]}')

    lines.append("\nWatch the attached clip and produce your candidate annotation now. Return STRICT JSON only.")
    return "\n".join(lines)


def call_gemini(clip, condition):
    youtube_url = f"https://www.youtube.com/watch?v={clip['video_id']}"
    prompt = build_user_prompt(clip, condition)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=types.Content(
                parts=[
                    types.Part(
                        file_data=types.FileData(
                            file_uri=youtube_url,
                            mime_type="video/*",
                        ),
                        video_metadata=types.VideoMetadata(
                            start_offset=f"{clip['start_seconds']}s",
                            end_offset=f"{clip['end_seconds']}s",
                        ),
                    ),
                    types.Part(text=prompt),
                ]
            ),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
        )
        text = response.text
        if not text:
            return {"error": "empty_response"}
        return json.loads(text)
    except Exception as e:
        return {"error": str(e)[:200]}


def main():
    results = []
    total = len(CLIPS) * len(CONDITIONS) * N_RUNS
    counter = 0

    # Open CSV in append mode · write header first, then append each row after each call
    fieldnames = ["clip", "condition", "run", "primary", "secondaries", "rationale_preview"]
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        f.flush()

    for clip in CLIPS:
        for cond in CONDITIONS:
            for run in range(1, N_RUNS + 1):
                counter += 1
                print(f"[{counter}/{total}] {clip['title']} · {cond} · run {run}", flush=True)
                res = call_gemini(clip, cond)
                if "error" in res:
                    row = {
                        "clip": clip["title"],
                        "condition": cond,
                        "run": run,
                        "primary": "ERROR",
                        "secondaries": "",
                        "rationale_preview": res["error"][:100],
                    }
                else:
                    secondaries = res.get("candidate_secondary_emotions", [])
                    rationale = res.get("candidate_rationale", "")
                    row = {
                        "clip": clip["title"],
                        "condition": cond,
                        "run": run,
                        "primary": res.get("candidate_primary_emotion", "MISSING"),
                        "secondaries": ",".join(secondaries) if secondaries else "",
                        "rationale_preview": rationale[:100],
                    }
                results.append(row)
                # Append row immediately · safe against crashes / uploads
                with open(OUTPUT_CSV, "a", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow(row)
                    f.flush()
                time.sleep(SLEEP_BETWEEN)

    print(f"\n✓ Done · {len(results)} rows saved to {OUTPUT_CSV}")

    print("\n=== Quick summary · primary emotion counts per (clip, condition) ===")
    for clip in CLIPS:
        for cond in CONDITIONS:
            primaries = [r["primary"] for r in results
                          if r["clip"] == clip["title"] and r["condition"] == cond]
            counts = Counter(primaries).most_common()
            mixed_n = sum(1 for p in primaries if p == "mixed_more_than_one")
            print(f"  {clip['title'][:22]:22} · {cond:22} · mixed={mixed_n}/{N_RUNS} · {counts}")


if __name__ == "__main__":
    main()
