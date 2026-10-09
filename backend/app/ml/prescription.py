import os
from openai import OpenAI

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"   # change if you prefer another


def _get_client():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key, timeout=30.0)


# Human-readable class descriptions used inside the prompt
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
    Call NVIDIA NIM to produce a short clinical draft prescription.
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

    response = client.chat.completions.create(
        model=NVIDIA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=400,
    )

    return response.choices[0].message.content.strip()