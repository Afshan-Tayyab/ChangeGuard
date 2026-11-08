# backend/services/semantic_analyzer.py
import spacy

nlp = spacy.load("en_core_web_sm")

def split_into_sentences(text: str) -> list[str]:
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

def analyze_sentence(sentence: str) -> dict:
    doc = nlp(sentence)
    
    analysis = {
        "original": sentence,
        "subject": [],
        "action": [],
        "object": [],
        "modality": [],
        "negation": False,
        "conditions": [],
        "deadlines": [],
        "restrictions": [],
        "exceptions": []
    }

    modals = {"must", "may", "should", "can", "will", "shall", "might", "could"}
    negations = {"not", "no", "never", "neither", "without", "cannot"}
    
    # 1. Find the index where the exception starts (e.g., "unless")
    exception_start_idx = 999
    for token in doc:
        if token.text.lower() in ("unless", "except", "excluding"):
            exception_start_idx = token.i
            # Grab the whole clause after the exception word
            phrase = " ".join([t.text for t in doc[token.i:]])
            analysis["exceptions"].append(phrase)

    # 2. Extract Restrictions (Capture the full noun phrase)
    for chunk in doc.noun_chunks:
        if "only" in chunk.text.lower() or "all" in chunk.text.lower():
            analysis["restrictions"].append(chunk.text.strip())
            
    # 3. Extract Modality and Negation
    for token in doc:
        if token.text.lower() in negations or token.text.endswith("n't"):
            analysis["negation"] = True
        if token.text.lower() in modals or token.tag_ == "MD":
            analysis["modality"].append(token.text.lower())

    # 4. Extract Deadlines (Dates and Times)
    # If it's a DATE or TIME, it's a deadline.
    for ent in doc.ents:
        if ent.label_ in ("DATE", "TIME"):
            analysis["deadlines"].append(ent.text)
        elif ent.label_ in ("PERCENT", "CARDINAL"):
            # Only treat as condition if it has a comparison word (above, below, least)
            prev_word = doc[ent.start - 1].text.lower() if ent.start > 0 else ""
            if prev_word in ("above", "below", "least", "greater", "less", "over", "under"):
                analysis["conditions"].append(f"{prev_word} {ent.text}")

    # 5. Extract Subject, Action, Object
    for token in doc:
        # STOP extracting objects if we are inside an exception clause!
        if token.i >= exception_start_idx:
            continue
            
        if token.dep_ in ("nsubj", "nsubjpass"):
            analysis["subject"].append(token.text)
            
        if token.pos_ == "VERB" and token.dep_ == "ROOT":
            analysis["action"].append(token.lemma_)
            
        if token.dep_ in ("dobj", "pobj"):
            # Exclude dates and restrictions from being objects
            is_date = any(ent.label_ in ("DATE", "TIME") for ent in doc.ents if token in ent)
            if not is_date:
                # Get the full noun phrase for the object (e.g., "examination fee")
                for chunk in doc.noun_chunks:
                    if token in chunk:
                        analysis["object"].append(chunk.text)
                        break
                else:
                    analysis["object"].append(token.text)

    # Clean up lists
    for key in analysis:
        if isinstance(analysis[key], list):
            analysis[key] = list(dict.fromkeys(analysis[key])) # Remove duplicates
            if not analysis[key]:
                analysis[key] = "None"

    return analysis