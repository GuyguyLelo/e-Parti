"""Context processors e-Parti / E.C.C.O."""


def eparti_context(request):
    return {
        "EPARTI_NAME": "e-Parti",
        "EPARTI_ORG": "E.C.C.O.",
        "EPARTI_SLOGAN": "Ensemble, Changeons le Congo",
        "EPARTI_COUNTRY": "République Démocratique du Congo",
    }
