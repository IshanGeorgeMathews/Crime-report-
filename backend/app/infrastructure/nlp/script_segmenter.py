import re
import unicodedata

def is_char_malayalam(char: str, context_prev: str = "", context_next: str = "") -> bool:
    """Return True if character belongs to Malayalam orthography.
    
    Checks the standard Malayalam range U+0D00 - U+0D7F (which includes vowels,
    consonants, digits, and Chillu characters U+0D7A-U+0D7F) and protects
    Zero-Width Joiner (ZWJ, U+200D) and Zero-Width Non-Joiner (ZWNJ, U+200C)
    if they are immediately adjacent to a Malayalam character.
    """
    if not char:
        return False
    codepoint = ord(char)
    # 1. Standard Malayalam Unicode block
    if 0x0D00 <= codepoint <= 0x0D7F:
        return True
    # 2. Zero-Width Joiner / Non-Joiner (protect only if adjacent to Malayalam)
    if codepoint in (0x200C, 0x200D):
        prev_is_ml = context_prev and (0x0D00 <= ord(context_prev) <= 0x0D7F)
        next_is_ml = context_next and (0x0D00 <= ord(context_next) <= 0x0D7F)
        return bool(prev_is_ml or next_is_ml)
    return False

def segment_by_script(text: str) -> list[tuple[str, str]]:
    """Segment text into contiguous script runs of 'ml' or 'en' (with neutralRuns absorbed).
    
    Alphanumeric ASCII characters are categorized as English ('en').
    Punctuation, symbols, and spaces are neutral and are absorbed into adjacent runs.
    ZWJ/ZWNJ adjacent to Malayalam characters are kept within the Malayalam run.
    """
    if not text:
        return []

    # Step 1: Label each character by script
    char_labels = []
    for i, char in enumerate(text):
        prev_char = text[i - 1] if i > 0 else ""
        next_char = text[i + 1] if i < len(text) - 1 else ""
        
        if is_char_malayalam(char, prev_char, next_char):
            label = "ml"
        elif char.isalnum() and ord(char) < 128:
            # ASCII alphanumeric is English
            label = "en"
        elif unicodedata.category(char).startswith("L") and not (0x0D00 <= ord(char) <= 0x0D7F):
            # Other non-Malayalam letters are English
            label = "en"
        else:
            label = "neutral"
        char_labels.append(label)

    # Step 2: Form initial contiguous runs
    runs = []
    current_text = ""
    current_label = ""

    for char, label in zip(text, char_labels):
        if not current_label:
            current_text = char
            current_label = label
        elif label == current_label:
            current_text += char
        else:
            runs.append((current_text, current_label))
            current_text = char
            current_label = label
    if current_text:
        runs.append((current_text, current_label))

    # Step 3: Absorb neutral runs into surrounding runs
    # We iterate and merge neutral runs with their neighbor.
    # Standard rule:
    # - A neutral run inherits the script of its preceding run.
    # - If it has no preceding run (start of text), it inherits the succeeding run.
    # - If the entire text is neutral, we treat it as 'en'.
    absorbed_runs = []
    
    for i, (run_text, label) in enumerate(runs):
        if label != "neutral":
            absorbed_runs.append((run_text, label))
        else:
            # Neutral run absorption
            if absorbed_runs:
                # Append to preceding run
                prev_text, prev_label = absorbed_runs[-1]
                absorbed_runs[-1] = (prev_text + run_text, prev_label)
            else:
                # No preceding run. Find next non-neutral run.
                next_label = "en"
                for j in range(i + 1, len(runs)):
                    if runs[j][1] != "neutral":
                        next_label = runs[j][1]
                        break
                absorbed_runs.append((run_text, next_label))

    # Step 4: Condense consecutive runs of same label
    condensed_runs = []
    for run_text, label in absorbed_runs:
        if not condensed_runs:
            condensed_runs.append((run_text, label))
        elif condensed_runs[-1][1] == label:
            prev_text, prev_label = condensed_runs[-1]
            condensed_runs[-1] = (prev_text + run_text, prev_label)
        else:
            condensed_runs.append((run_text, label))

    return condensed_runs
