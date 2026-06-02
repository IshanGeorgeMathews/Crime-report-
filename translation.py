import os
import re
import json
import unicodedata
from deep_translator import GoogleTranslator
from script_segmenter import segment_by_script

# ---------------------------------------------------------------------------
# Malayalam Proper Suffix Disambiguation Constants & Regex
# ---------------------------------------------------------------------------

# Singular-only matching patterns for name suffixes
KUTTY_SUFFIX_RE = re.compile(r"^കുട്ടി(യെ|യുടെ|ക്ക്|യോട്|യിൽ|യാൽ)?$")
PILLAI_SUFFIX_RE = re.compile(r"^പിള്ള(യെ|യുടെ|യ്ക്ക്|യോട്|യിൽ|യാൽ)?$")

# Matches relative adjectival participles (verbs that end in typical Malayalam adjectival terminations)
MALAYALAM_PARTICIPLE_PATTERN = re.compile(
    r".*(യായ|പ്പെട്ട|ിച്ച|പ്പട്ട|ച്ച|ത്ത|േറ്റ|ാത|ായവൻ|ായവൾ|കടത്തിയ|പിടിച്ച|വിറ്റ)$"
)

# Baseline exclusions for child reference common nouns
MALAYALAM_COMMON_EXCLUSIONS = {
    # Pronouns & Specifiers
    "ഈ", "ആ", "ഏത്", "അവൻ", "Avath", "അവൾ", "അവർ", "അത്", "ഇത്", "യതൊരു", "മറ്റ്", "മറ്റുള്ള", "മറ്റു",
    # Numbers & Quantifiers
    "ഒരു", "രണ്ട്", "മൂന്ന്", "നാല്", "അഞ്ച്", "രണ്ടു", "മൂന്നു", "നാലു", "അഞ്ചു", "പത്ത്",
    "ഒരുപാട്", "നിരവധി", "ചില", "പല", "ചിലർ", "പലർ", "കുറച്ചു", "കുറഞ്ഞ", "കൂടുതൽ", "കുറേ", "കുറെ", "ഓരോ", "ആകെ",
    # Adjectives
    "മൂത്ത", "ഇളയ", "ചെറിയ", "വലിയ", "കൊച്ചു", "നല്ല", "ചീത്ത", "പാവം", "കുഞ്ഞ്", "കുഞ്ഞ",
    # Relative Participles (Common in general police texts)
    "ചെയ്ത", "പറഞ്ഞ", "കണ്ട", "പോയ", "വന്ന", "നിന്ന", "ഉണ്ടായ", "ആയ", "തൂങ്ങിമരിച്ച",
    "അറസ്റ്റ്", "കസ്റ്റഡിയിൽ", "പ്രതിയായ", "പിടികൂടിയ", "ഓടിപ്പോയ", "മരിച്ച", "കൊല്ലപ്പെട്ട",
    "കാണാനില്ല", "കണ്ടെത്തി", "ചേർന്ന", "നടന്ന", "നടത്തിയ", "ഉപയോഗിച്ച", "എത്തിയ", "വാങ്ങിയ",
    # Victim-specific Relative Participles (Valayar case safeguard)
    "ഇരയായ", "ഇരകളായ", "ഇരയായവൻ", "ഇരയായവൾ", "പരിക്കേറ്റ", "പീഡിപ്പിക്കപ്പെട്ട", "ചൂഷണം ചെയ്യപ്പെട്ട",
    "അതിക്രമത്തിനിരയായ", "അക്രമത്തിനിരയായ", "പീഡനത്തിനിരയായ", "ക്രൂരതയ്ക്കിരയായ",
    # Conjunctions / Particles
    "എന്നിങ്ങനെ", "എന്ന്", "എന്നിട്ട്", "എന്നാൽ", "പക്ഷേ", "കൂടാതെ", "അതിനാൽ", "മാത്രം"
}

def load_exclusions() -> set:
    """Load baseline exclusions and merge them with exclusions_override.json if present."""
    exclusions = set(MALAYALAM_COMMON_EXCLUSIONS)
    override_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exclusions_override.json")
    if os.path.isfile(override_path):
        try:
            with open(override_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    exclusions.update(data)
                    print(f"[Info] Loaded {len(data)} custom exclusions from exclusions_override.json")
        except Exception as e:
            print(f"[Warning] Failed to load exclusions override: {e}")
    return exclusions

# ---------------------------------------------------------------------------
# Suffix Anchoring Algorithm
# ---------------------------------------------------------------------------

def anchor_malayalam_suffixes(text: str) -> str:
    """Pre-translation suffix anchoring algorithm (PTSR Pass 1).
    
    Checks singular inflected forms of 'കുട്ടി' and 'പിള്ള'. Applies
    backward-scanning context evaluation. If the suffix is preceded by
    adjectives, relative participles, or boundaries, it is NOT anchored.
    """
    if not text:
        return text

    # Tokenize the text, separating word runs, punctuation, whitespace runs and newlines
    # Pattern extracts: Malayalam words, English words, newlines, spaces, or individual punctuation
    token_pattern = re.compile(r"[\u0D00-\u0D7F]+|[a-zA-Z0-9]+|\n|[^\w\s]|\s+")
    tokens = token_pattern.findall(text)
    
    # Load dynamic exclusions
    exclusions = load_exclusions()
    
    new_tokens = list(tokens)
    
    for i, token in enumerate(tokens):
        # 1. Match name suffixes
        is_kutty = KUTTY_SUFFIX_RE.match(token)
        is_pillai = PILLAI_SUFFIX_RE.match(token)
        
        if not (is_kutty or is_pillai):
            continue
            
        # 2. Backward scan to find the immediate preceding Malayalam word run
        anchor = True
        preceding_word = ""
        
        for j in range(i - 1, -1, -1):
            prev_token = tokens[j]
            
            # Skip only whitespace (single space or tabs)
            if prev_token.isspace() and prev_token != "\n" and len(prev_token) <= 2:
                continue
                
            # If we hit punctuation, newlines, or sentence-ending boundaries, abort
            is_boundary = prev_token == "\n" or any(unicodedata.category(c)[0] in ("P", "S", "Z", "C") for c in prev_token)
            if is_boundary:
                anchor = False
                break
                
            # Found a Malayalam word token
            if re.match(r"^[\u0D00-\u0D7F]+$", prev_token):
                preceding_word = prev_token
                break
            else:
                # English or mixed digit run
                anchor = False
                break
        
        # 3. Apply validation gates
        if not preceding_word:
            anchor = False
            
        if anchor:
            # Check exclusions list
            if preceding_word in exclusions:
                anchor = False
            # Check digit rules
            elif preceding_word.isdigit():
                anchor = False
            # Check unsupervised relative participle endings (e.g. -aaya, -ppetta)
            elif MALAYALAM_PARTICIPLE_PATTERN.match(preceding_word):
                anchor = False
                
        # 4. Perform substitution if anchored
        if anchor:
            replacement = "Kutty" if is_kutty else "Pillai"
            new_tokens[i] = replacement

    return "".join(new_tokens)

# ---------------------------------------------------------------------------
# Lazy-Loaded IndicTrans2 Translation Engine
# ---------------------------------------------------------------------------

class TranslationEngine:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TranslationEngine, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.tokenizer = None
            cls._instance.device = None
            cls._instance.initialized = False
            cls._instance.indic_attempted = False
        return cls._instance

    def initialize_indictrans(self):
        """Lazy load IndicTrans2 model if possible."""
        if os.environ.get("DISABLE_INDIC_TRANS") == "1":
            return False
        if self.initialized:
            return True
        if self.indic_attempted:
            return False
        self.indic_attempted = True
            
        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            
            print("  [IndicTrans2] Loading ai4bharat/indictrans2-indic-en-1B model...")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            model_name = "ai4bharat/indictrans2-indic-en-1B"
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                model_name, 
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            ).to(self.device)
            self.model.eval()
            self.initialized = True
            print(f"  [IndicTrans2] Model loaded successfully on {self.device}.")
            return True
        except Exception as e:
            print(f"  [Warning] IndicTrans2 loading failed: {e}. Operating in fallback mode.")
            self.initialized = False
            return False

    def translate_segment(self, text: str, src_lang: str = "mal_Mlym") -> str:
        """Translate a single string run.
        
        Attempts IndicTrans2 first, and falls back to Google Translate.
        Returns the translated segment and the engine name used.
        """
        if not text or not text.strip():
            return text, "none"

        # Try local IndicTrans2
        if self.initialize_indictrans():
            try:
                import torch
                # Format for IndicTrans2 tokenizer
                inputs = self.tokenizer(
                    [text], 
                    src_lang=src_lang, 
                    tgt_lang="eng_Latn", 
                    return_tensors="pt"
                ).to(self.device)
                
                with torch.no_grad():
                    generated_tokens = self.model.generate(
                        **inputs,
                        num_beams=4,
                        max_length=256
                    )
                
                outputs = self.tokenizer.batch_decode(
                    generated_tokens, 
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=True
                )
                return outputs[0].strip(), "indictrans"
            except Exception as e:
                print(f"  [Warning] IndicTrans2 translation error: {e}. Falling back.")

        # Fallback to deep-translator (Google Free)
        try:
            translated = GoogleTranslator(source="ml", target="en").translate(text)
            return translated or text, "google"
        except Exception as e:
            print(f"  [Error] Fallback Google Translate failed: {e}")
            return text, "failed"

    def translate_document(
        self,
        text: str,
        use_ollama: bool = False,
        ollama_url: str = "http://localhost:11434",
        batch_engines: list = None,
    ) -> str:
        """Translates mixed-script raw text.
        
        1. Segment text by script (protect English runs).
        2. Applies pre-translation suffix anchoring on Malayalam runs.
        3. Translates Malayalam runs chunk by chunk using translate_segment.
        4. Reassembles runs in original order.
        5. Logs engine consistency tracking.

        IndicTrans2 is always the primary translator. ``use_ollama`` and
        ``ollama_url`` are accepted for compatibility with the older wrapper;
        Ollama is used later for summarization, not raw translation.
        """
        if not text or not text.strip():
            return text

        # Step 1: Script Segmentation
        segments = segment_by_script(text)
        translated_segments = []
        
        for run_text, script in segments:
            if script == "en":
                # Protected Latin block - passthrough
                translated_segments.append(run_text)
            else:
                # Malayalam block
                # Step 2: Suffix Anchoring pre-translation
                anchored_run = anchor_malayalam_suffixes(run_text)
                
                # Step 3: Chunking & Translation
                chunks = self._chunk_malayalam_text(anchored_run, max_tokens=150)
                translated_chunks = []
                
                for chunk in chunks:
                    if not chunk.strip():
                        translated_chunks.append(chunk)
                        continue
                    
                    trans_text, engine = self.translate_segment(chunk)
                    translated_chunks.append(trans_text)
                    
                    if batch_engines is not None:
                        batch_engines.append(engine)
                
                translated_segments.append(" ".join(translated_chunks))

        return " ".join(translated_segments)

    def _chunk_malayalam_text(self, text: str, max_tokens: int = 150) -> list:
        """Splits Malayalam run into smaller pieces at sentence boundary patterns."""
        # IndicTrans2 inputs are ideally sentence-length to maintain translation accuracy
        if len(text) < 400:
            return [text]
            
        chunks = []
        current = ""
        
        # Split on sentence terminals
        sentences = re.split(r"(?<=[.!?\u0D7F])\s+", text)
        for sentence in sentences:
            # Rough character-based estimate of BPE tokens (4 chars = 1 token roughly)
            if len(current) + len(sentence) + 1 > max_tokens * 4:
                if current:
                    chunks.append(current)
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
                
        if current:
            chunks.append(current)
            
        return chunks or [text]
