import os
import time
from google import genai
from google.genai import types

PRIMARY_MODEL  = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash"


def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)


CLASS_DESCRIPTIONS = {
    "mel":  "Melanoma — a malignant tumor of melanocytes. Most dangerous skin cancer; requires urgent biopsy and staging.",
    "bcc":  "Basal Cell Carcinoma — most common skin cancer. Locally invasive; rarely metastasizes. Usually treated with surgical excision or topical therapy.",
    "akiec":"Actinic Keratosis / Bowen's Disease — premalignant or in-situ squamous lesion. Risk of progression to invasive SCC. Treated with cryotherapy, topical 5-FU, imiquimod, or PDT.",
    "bkl":  "Benign Keratosis-like lesion — seborrheic keratosis or solar lentigo. Benign; cosmetic concern only.",
    "df":   "Dermatofibroma — benign fibrous nodule. No treatment required unless symptomatic.",
    "nv":   "Melanocytic Nevus — common benign mole. No treatment required; monitor for changes.",
    "vasc": "Vascular lesion — hemangioma or angiokeratoma. Usually benign; treat if bleeding or cosmetic concern.",
}

# Malignant classes force a biopsy-first recommendation
MALIGNANT = {"mel", "bcc", "akiec"}


def _call_gemini(client, model, system_prompt, user_prompt, attempts=3):
    last_err = None
    for i in range(attempts):
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=900,
                ),
            )
            return response.text.strip()
        except Exception as e:
            last_err = e
            msg = str(e)
            if ("503" in msg or "429" in msg
                    or "UNAVAILABLE" in msg or "RESOURCE_EXHAUSTED" in msg):
                wait = 2 ** i
                print(f"[gemini] transient error on {model} (attempt {i+1}/{attempts}), retrying in {wait}s")
                time.sleep(wait)
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

    description = CLASS_DESCRIPTIONS.get(predicted_class, "Unknown lesion class.")
    is_malignant = predicted_class in MALIGNANT

    patient_bits = []
    if patient_age:
        patient_bits.append(f"age {patient_age}")
    if patient_sex:
        patient_bits.append(patient_sex)
    if lesion_site:
        patient_bits.append(f"lesion on {lesion_site}")
    patient_summary = ", ".join(patient_bits) if patient_bits else "no patient metadata provided"

    system_prompt = (
        "You are a licensed dermatologist writing a formal clinical note for a "
        "patient record. Your output will be reviewed and co-signed by the "
        "attending physician. Never mention AI, machine learning, or the model. "
        "Never hedge. Write in the voice of a senior clinician. "
        "Use exactly the numbered structure requested. Be complete: every "
        "section must contain at least one full sentence. No bullet points "
        "shorter than 8 words. Finish with the disclaimer line exactly as "
        "instructed."
    )

    user_prompt = f"""Patient record — dermoscopy review.

Classification:
  Diagnosis        : {predicted_class} ({description})
  Model confidence : {confidence:.1%}
  Triage category  : {binary_label} ({binary_confidence:.1%})
  Patient          : {patient_summary}
  Malignancy flag  : {"MALIGNANT — urgent pathway" if is_malignant else "Benign — routine pathway"}

Write the clinical note in EXACTLY this numbered format. Each numbered
section must have at least one full sentence (2–4 lines). Do not skip any
section. Do not use bullet points. Do not shorten.

1. CLINICAL ASSESSMENT
   Describe the lesion as it presents in the dermoscopy image, referencing
   the predicted diagnosis ({predicted_class}), the confidence level, and
   the visual features that support the classification. State whether the
   features are concerning for malignancy.

2. DIAGNOSTIC PLAN
   State the required histopathological or imaging confirmation.
   {"Order an urgent excisional biopsy with margin control. Include Breslow thickness, Clark level, and margin status in the pathology request." if is_malignant else "If the lesion is stable and asymptomatic, no biopsy is required; document baseline morphology for future comparison."}

3. TREATMENT PLAN
   {"Refer for urgent surgical excision. Do not use topical therapies before histological confirmation." if is_malignant else "No active treatment indicated. If cosmetically bothersome, options include shave excision, cryotherapy, or observation."}

4. MEDICATIONS
   List specific topical or systemic agents with strength and frequency
   if applicable. If no medication is required, state that clearly.

5. PATIENT COUNSELLING
   Describe what the patient should be told: sun protection, warning
   signs to watch for, and when to return.

6. FOLLOW-UP
   {"Review in 2–4 weeks with biopsy results. Refer to oncology if melanoma or high-risk BCC is confirmed." if is_malignant else "Review in 6–12 months, or sooner if the lesion changes in size, shape, or colour."}

7. DISCLAIMER
   Exactly this line: "This is a draft clinical note generated for research purposes; final diagnosis and prescription require review and approval by a licensed physician."
"""

    try:
        return _call_gemini(client, PRIMARY_MODEL, system_prompt, user_prompt)
    except Exception as e:
        print(f"[gemini] primary failed: {repr(e)[:200]}")
        print(f"[gemini] falling back to {FALLBACK_MODEL}")
        return _call_gemini(client, FALLBACK_MODEL, system_prompt, user_prompt, attempts=2)