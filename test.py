from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "ai4bharat/indictrans2-indic-en-1B"

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

print("Loading model...")
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, trust_remote_code=True)

print("SUCCESS")