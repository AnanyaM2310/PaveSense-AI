from transformers import pipeline

language_classifier = pipeline(
    "text-classification",
    model="papluca/xlm-roberta-base-language-detection"
)


LANGUAGE_MAP = {

    "en": "en",
    "ml": "ml",
    "hi": "hi",
    "ta": "ta",
    "te": "te",
    "kn": "kn",
    "mr": "mr",
    "bn": "bn",
    "gu": "gu",
    "pa": "pa",
    "or": "or",
    "as": "as",
    "ur": "ur",
    "ne": "ne",
    "sd": "sd"

}


def detect_language(text):

    prediction = language_classifier(text)

    language = prediction[0]["label"]

    return LANGUAGE_MAP.get(language, "en")