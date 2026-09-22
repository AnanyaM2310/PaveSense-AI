from transformers import AutoTokenizer
from transformers import AutoModelForSeq2SeqLM

MODEL_NAME = "facebook/nllb-200-distilled-600M"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


# ===============================
# Language Mapping
# ===============================

LANGUAGE_CODES = {

    "en": "eng_Latn",
    "ml": "mal_Mlym",
    "hi": "hin_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "kn": "kan_Knda",
    "mr": "mar_Deva",
    "bn": "ben_Beng",
    "gu": "guj_Gujr",
    "pa": "pan_Guru",
    "or": "ory_Orya",
    "as": "asm_Beng",
    "ur": "urd_Arab",
    "ne": "npi_Deva",
    "sd": "snd_Arab",
    "kok": "gom_Deva",
    "doi": "doi_Deva",
    "mai": "mai_Deva",
    "mni": "mni_Beng",
    "sa": "san_Deva",
    "sat": "sat_Olck",
    "brx": "brx_Deva"

}


# ===============================
# Translation Function
# ===============================

def translate_to_english(text, source_language):

    source = LANGUAGE_CODES.get(source_language)

    if source is None:
        return text

    tokenizer.src_lang = source

    encoded = tokenizer(
        text,
        return_tensors="pt"
    )

    generated = model.generate(
        **encoded,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids("eng_Latn"),
        max_length=512
    )

    translated_text = tokenizer.batch_decode(
        generated,
        skip_special_tokens=True
    )[0]

    return translated_text

