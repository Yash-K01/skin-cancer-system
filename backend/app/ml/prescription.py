import os
import time
from google import genai
from google.genai import types

PRIMARY_MODEL  = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash"

MALIGNANT = {"mel", "bcc", "akiec"}


def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=25_000),
    )


CLASS_DESCRIPTIONS = {
    "mel":   "Melanoma",
    "bcc":   "Basal Cell Carcinoma",
    "akiec": "Actinic Keratosis / Bowen's Disease",
    "bkl":   "Benign Keratosis",
    "df":    "Dermatofibroma",
    "nv":    "Melanocytic Nevus (common mole)",
    "vasc":  "Vascular Lesion",
}


def _call_gemini(client, model, system_prompt, user_prompt, attempts=3):
    last_err = None
    for i in range(attempts):
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=4000,
                ),
            )
            if response.candidates:
                print(f"[gemini] finish_reason: {response.candidates[0].finish_reason}", flush=True)
            text = response.text.strip()
            # If the response was cut off, warn
            if response.candidates and str(response.candidates[0].finish_reason) == "FinishReason.MAX_TOKENS":
                print("[gemini] WARNING: output truncated by max_output_tokens", flush=True)
            return text
        except Exception as e:
            last_err = e
            msg = str(e)
            if any(t in msg for t in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED")):
                time.sleep(2 ** i)
                continue
            raise
    raise last_err


def _build_prompts(disease, is_malignant, patient_summary, confidence, binary_label, section_range):
    system_prompt = (
        "You are a dermatologist writing a plain-English prescription for a "
        "patient. Output ONLY the final prescription text. "
        "Do NOT output your reasoning, notes, drafts, checklists, or any "
        "meta-commentary. Do NOT use markdown, asterisks, hash symbols, or "
        "bullet points. Use plain sentences and simple headings in ALL CAPS "
        "followed by a colon. Never mention AI, the model, or that you are "
        "an assistant. Write as if handing the note directly to the patient. "
        "Every heading must be followed by at least 2 and at most 4 complete "
        "sentences. Do not stop mid-sentence."
    )

    sections = {
        1: f"""WHAT YOU HAVE:
Explain in two short sentences what {disease} is. Say whether it is
{"serious and needs urgent care" if is_malignant else "usually harmless"}. Write at least 3 full sentences.""",

        2: f"""WHAT THIS MEANS FOR YOU:
Explain the next step. {"A small sample will be removed for testing. Your doctor will arrange this quickly." if is_malignant else "This can usually be left alone and simply watched over time."} Write at least 3 full sentences.""",

        3: """WHAT YOU SHOULD DO:
Write 4 complete sentences describing what the patient should do. Each sentence must be at least 10 words. Examples: keep the area clean and dry, do not scratch or pick the lesion, take monthly photos to track changes, avoid sharing towels, wear loose clothing.""",

        4: """WHAT YOU SHOULD AVOID:
Write 4 complete sentences describing what the patient should avoid. Each sentence must be at least 10 words. Examples: avoid direct sun on the lesion, do not use home remedies, do not apply unknown creams, do not shave over the area, avoid tight clothing that rubs.""",

        5: """FOOD AND DRINK:
Write 4 complete sentences. Suggest foods that help the skin: leafy greens, tomatoes, carrots, berries, nuts, fatty fish. Suggest foods to limit: sugary drinks, fried food, excess alcohol. Mention drinking 2 to 3 litres of water daily.""",

        6: f"""SOAP, CREAM AND PRODUCTS TO USE:
Write 4 complete sentences. Recommend a mild fragrance-free cleanser (Cetaphil or CeraVe). Recommend a light moisturiser (CeraVe or Cetaphil). Recommend sunscreen SPF 50+. {"State that no prescription cream should be used until the biopsy is complete." if is_malignant else "State that no prescription cream is needed for this lesion."}""",

        7: """SUN PROTECTION:
Write 4 complete sentences. Explain sunscreen SPF 50+, reapply every 2 hours outdoors, wide-brimmed hat, long sleeves, avoid the sun between 11 in the morning and 4 in the afternoon.""",

        8: f"""WHEN TO RETURN TO THE DOCTOR:
Write 3 complete sentences. {"Return within 2 weeks for biopsy results. Go to the emergency department if the lesion bleeds, grows quickly, or becomes painful." if is_malignant else "Return in 6 to 12 months, or sooner if the mole changes in size, shape, colour, or starts to itch or bleed."}""",

        9: """DISCLAIMER:
Write exactly this sentence and nothing else: This is a computer-generated draft. It must be reviewed and approved by your doctor before use.""",
    }

    parts = [sections[i] for i in section_range]
    body = "\n\n".join(parts)

    user_prompt = f"""Write a skin care prescription for a patient.

Diagnosis: {disease}
Risk: {binary_label}
Confidence: {confidence:.1%}
Patient: {patient_summary}

Use the headings below. Each heading on its own line in ALL CAPS followed
by a colon. Under each heading write the requested number of sentences.
No markdown, no asterisks, no bullet points, no numbered sublists, no
notes about what you are doing.

{body}

Write every sentence completely. Do not stop mid-sentence. Do not skip
any heading.
"""
    return system_prompt, user_prompt


def generate_prescription(predicted_class: str,
                          confidence: float,
                          binary_label: str,
                          binary_confidence: float,
                          patient_age: int = None,
                          patient_sex: str = None,
                          lesion_site: str = None) -> str:
    client = _get_client()

    disease = CLASS_DESCRIPTIONS.get(predicted_class, "Unknown lesion")
    is_malignant = predicted_class in MALIGNANT

    patient_bits = []
    if patient_age:  patient_bits.append(f"age {patient_age}")
    if patient_sex:  patient_bits.append(patient_sex)
    if lesion_site:  patient_bits.append(f"on the {lesion_site}")
    patient_summary = ", ".join(patient_bits) if patient_bits else "not specified"

    # ---- Call 1: sections 1-5 ----
    sys1, usr1 = _build_prompts(
        disease, is_malignant, patient_summary, confidence, binary_label,
        section_range=[1, 2, 3, 4, 5],
    )
    try:
        part1 = _call_gemini(client, PRIMARY_MODEL, sys1, usr1)
    except Exception as e:
        print(f"[gemini] primary failed (part 1): {repr(e)[:200]}", flush=True)
        part1 = _call_gemini(client, FALLBACK_MODEL, sys1, usr1, attempts=2)

    # ---- Call 2: sections 6-9 ----
    sys2, usr2 = _build_prompts(
        disease, is_malignant, patient_summary, confidence, binary_label,
        section_range=[6, 7, 8, 9],
    )
    try:
        part2 = _call_gemini(client, PRIMARY_MODEL, sys2, usr2)
    except Exception as e:
        print(f"[gemini] primary failed (part 2): {repr(e)[:200]}", flush=True)
        part2 = _call_gemini(client, FALLBACK_MODEL, sys2, usr2, attempts=2)

    full = part1.strip() + "\n\n" + part2.strip()

    # Safety: ensure the disclaimer is present. If the second call dropped
    # it, append it verbatim.
    if "computer-generated draft" not in full.lower():
        full += ("\n\nDISCLAIMER:\n"
                 "This is a computer-generated draft. It must be reviewed "
                 "and approved by your doctor before use.")

    return full