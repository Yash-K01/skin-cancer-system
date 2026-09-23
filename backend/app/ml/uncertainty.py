import numpy as np
from app.config import settings


def softmax_entropy(probs):
    p = np.clip(probs, 1e-9, 1.0)
    return float(-(p * np.log(p)).sum())


def uncertainty_report(probs):
    top1 = float(probs.max())
    sorted_p = np.sort(probs)
    top2 = float(sorted_p[-2]) if len(sorted_p) > 1 else 0.0
    margin = top1 - top2
    entropy = softmax_entropy(probs)

    reasons = []
    if top1 < settings.CONFIDENCE_MIN:
        reasons.append("low_confidence")
    if margin < settings.MARGIN_MIN:
        reasons.append("ambiguous_margin")
    if entropy > settings.ENTROPY_MAX:
        reasons.append("high_entropy")

    if reasons:
        return {
            "status": "uncertain",
            "reason": ",".join(reasons),
            "top1": top1,
            "top2": top2,
            "margin": margin,
            "entropy": entropy,
        }

    return {
        "status": "ok",
        "reason": "confident",
        "top1": top1,
        "top2": top2,
        "margin": margin,
        "entropy": entropy,
    }