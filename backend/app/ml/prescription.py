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
        "You are writing a patient-friendly skin care prescription in simple "
        "English that a non-medical person can understand. No jargon. "
        "Short sentences. Clear headings. Never mention AI or the model. "
        "Your goal is to tell the patient exactly what they have, what they "
        "must do, what to avoid, what to eat, and which products to use."
    )

    user_prompt = f"""A patient has been evaluated by dermoscopy.

Findings:
  Diagnosis       : {disease} ({predicted_class})
  Risk category   : {binary_label}
  Model confidence: {confidence:.1%}
  Patient         : {patient_summary}

Write the prescription in EXACTLY this format. Every section must have
at least 2–4 sentences. Do not use bullet points shorter than a full
sentence. Do not skip any section.

1. WHAT YOU HAVE
   Explain the diagnosis ({disease}) in one or two plain sentences.
   Say whether it is {"serious and needs urgent care" if is_malignant else "usually harmless and does not need to be removed"}.

2. WHAT THIS MEANS FOR YOU
   Explain what will happen next in simple terms. {"This needs a small procedure to remove a sample for testing. Your doctor will refer you quickly." if is_malignant else "This can be left alone and simply watched over time. It is not dangerous."}

3. WHAT YOU SHOULD DO
   Give 3–5 concrete actions. Examples: keep the area clean and dry, do
   not scratch or pick the lesion, take clear photos every month to
   track changes, avoid sharing towels, etc.

4. WHAT YOU SHOULD AVOID
   List what not to do. Examples: avoid direct sun on the lesion, do
   not use home remedies, do not apply unknown creams, do not shave
   over the area, avoid tight clothing rubbing on it.

5. FOOD AND DRINK
   Suggest foods that support skin health: leafy greens, tomatoes,
   carrots, berries, nuts, fatty fish, plenty of water. Suggest what to
   limit: sugary drinks, fried food, excess alcohol. Keep it practical.

6. SOAP, CREAM AND PRODUCTS TO USE
   Recommend specific types of products with generic names. Examples:
   a mild fragrance-free cleanser (Cetaphil, CeraVe, or similar),
   a broad-spectrum sunscreen SPF 50+, a simple moisturiser, and if
   relevant a prescribed topical medicine with strength and how often
   to apply it. {"No topical medicine should be applied until the biopsy is done." if is_malignant else "No prescription medicine is required for this lesion."}

7. SUN PROTECTION
   Explain how to protect the skin: SPF 50+, reapply every 2 hours,
   wide-brimmed hat, long sleeves, avoid 11 am – 4 pm sun.

8. WHEN TO RETURN TO THE DOCTOR
   {"Return within 2 weeks for the biopsy results. Go to the emergency department immediately if the lesion bleeds, grows quickly, or becomes painful." if is_malignant else "Return in 6–12 months for a routine check, or sooner if the mole changes in size, shape, colour, or starts to itch or bleed."}

9. DISCLAIMER
   Exactly this line: "This is a computer-generated draft. It must be reviewed and approved by your doctor before use."
"""

    try:
        return _call_gemini(client, PRIMARY_MODEL, system_prompt, user_prompt)
    except Exception as e:
        print(f"[gemini] primary failed: {repr(e)[:200]}", flush=True)
        return _call_gemini(client, FALLBACK_MODEL, system_prompt, user_prompt, attempts=2)