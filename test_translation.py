print("Step 1: Importing detector...")

from app.ai.language_detector import detect_language

print("✓ Language detector loaded")

print("Step 2: Importing translator...")

from app.ai.translator import translate_to_english

print("✓ Translator loaded")

print("Step 3: Ready for input")

text = input("Enter complaint: ")

print("Input received.")

language = detect_language(text)

print("Detected Language:", language)

english = translate_to_english(text, language)

print("English Translation:")

print(english)
