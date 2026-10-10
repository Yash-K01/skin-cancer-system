import os
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.8-flash"


def _get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    return genai.Client(api_key=api_key)


CLASS_DESCRIPTIONS = {
    "mel":  "Melanoma — a malignant tumor of melanocytes. The most dangerous skin cancer; requires urgent biopsy and staging.",
    "bcc":  "Basal Cell Carcinoma — the most common skin cancer. Locally invasive but rarely metastasizes. Usually treated with surgical excision or topical therapy.",
    "akiec":"Actinic Keratosis / Bowen's Disease — a premalignant or in-situ squamous lesion. Risk of progression to invasive SCC. Treated with cryotherapy, topical 5-FU, imiquimod, or PDT.",
    "bkl":  "Benign Keratosis-like lesion — includes seborrheic keratosis and solar lentigo. Benign, cosmetic concern only.",
    "df":   "Dermatofibroma — a benign fibrous nodule. No treatment required unless symptomatic.",
    "nv":   "Melanocytic Nevus — a common benign mole. No treatment required; monitor for changes.",
    "vasc": "Vascular lesion — includes hemangioma and angiokeratoma. Usually benign; treat if bleeding or cosmetic concern.",
}


def generate_prescription(predicted_class: str,
                          confidence: float,
                          binary_label: str,
                          binary_confidence: float,
                          patient_age: int = None,
                          patient_sex: str = None,
                          lesion_site: str = None) -> str:
    """
    Call Google Gemini to produce a short clinical draft prescription.
    """
    client = _get_client()

    description = CLASS_DESCRIPTIONS.get(
        predicted_class, "Unknown lesion class."
    )

    patient_bits = []
    if patient_age:
        patient_bits.append(f"age {patient_age}")
    if patient_sex:
        patient_bits.append(patient_sex)
    if lesion_site:
        patient_bits.append(f"lesion on {lesion_site}")
    patient_summary = ", ".join(patient_bits) if patient_bits else "no patient metadata provided"

    system_prompt = (
        "You are a clinical decision-support assistant for dermatology. "
        "You produce short, structured draft prescriptions for a licensed "
        "dermatologist to review. You MUST NOT diagnose independently — you "
        "only suggest next steps based on the AI classification provided. "
        "Keep the output under 180 words. Use plain clinical English. "
        "Never mention that you are an AI. Always end with a one-line "
        "disclaimer that this is a draft and requires physician approval."
    )

    user_prompt = f"""The AI dermoscopy model classified this lesion as:

  Predicted class : {predicted_class}
  Description     : {description}
  Confidence      : {confidence:.1%}
  Binary triage   : {binary_label} ({binary_confidence:.1%})

Patient context: {patient_summary}.

Produce a short draft prescription containing:
1. Assessment line — restate the class and confidence.
2. Recommended next step (biopsy / referral / topical / observation).
3. Suggested topical or systemic agent (name and typical use) if appropriate.
4. Follow-up interval.
5. Draft disclaimer line.

Keep it clinical and concise.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=400,
        ),
    )

    return response.text.strip()