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
                    max_output_tokens=1200,
                ),
            )
            return response.text.strip()
        except Exception as e:
            last_err = e
            msg = str(e)
            if any(t in msg for t in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED")):
                time.sleep(2 ** i)
                continue
            raise
    raise last_err


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

    system_prompt = (
        "You are a dermatologist writing a plain-English prescription for a "
        "patient. Output ONLY the final prescription text. "
        "Do NOT output your reasoning, notes, drafts, checklists, or any "
        "meta-commentary. Do NOT use markdown, asterisks, hash symbols, or "
        "bullet points. Use plain sentences and simple headings in ALL CAPS "
        "followed by a colon. Never mention AI, the model, or that you are "
        "an assistant. Write as if handing the note directly to the patient."
    )

    user_prompt = f"""Write a skin care prescription for a patient.

Diagnosis: {disease}
Risk: {binary_label}
Confidence: {confidence:.1%}
Patient: {patient_summary}

Use exactly these nine headings, in this order, each on its own line
in ALL CAPS followed by a colon. Under each heading write 2 to 4 plain
sentences. No markdown. No asterisks. No bullet points. No numbered
sublists. No notes about what you are doing.

WHAT YOU HAVE:
Explain in two short sentences what {disease} is. Say whether it is
{"serious and needs urgent care" if is_malignant else "usually harmless"}.

WHAT THIS MEANS FOR YOU:
Explain the next step. {"A small sample will be removed for testing. Your doctor will arrange this quickly." if is_malignant else "This can usually be left alone and simply watched over time."}

WHAT YOU SHOULD DO:
List 3 to 5 things to do, each as a full sentence.

WHAT YOU SHOULD AVOID:
List 3 to 5 things to avoid, each as a full sentence.

FOOD AND DRINK:
Suggest foods that help the skin and foods to limit. Full sentences only.

SOAP, CREAM AND PRODUCTS TO USE:
Recommend specific types of products with common brand names. If a
prescription cream is needed, give its name, strength, and how often
to apply. {"No prescription cream should be used until the biopsy is complete." if is_malignant else "No prescription cream is needed for this lesion."}

SUN PROTECTION:
Explain sunscreen and clothing protection in 3 to 4 sentences.

WHEN TO RETURN TO THE DOCTOR:
State a clear follow-up window and any warning signs that need urgent review. {"Return within 2 weeks for biopsy results. Go to the emergency department if the lesion bleeds, grows quickly, or becomes painful." if is_malignant else "Return in 6 to 12 months, or sooner if the mole changes in size, shape, colour, or starts to itch or bleed."}

DISCLAIMER:
Write exactly this sentence: This is a computer-generated draft. It must be reviewed and approved by your doctor before use.

Begin immediately with "WHAT YOU HAVE:". Do not write anything before it.
"""

    try:
        return _call_gemini(client, PRIMARY_MODEL, system_prompt, user_prompt)
    except Exception as e:
        print(f"[gemini] primary failed: {repr(e)[:200]}", flush=True)
        return _call_gemini(client, FALLBACK_MODEL, system_prompt, user_prompt, attempts=2)