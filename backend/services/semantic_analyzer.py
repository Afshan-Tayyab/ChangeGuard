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

    # 4. Extract Conditions and Deadlines
    comparison_words = {"above", "below", "least", "greater", "less", "over", "under", "before", "after"}
    
    # First pass: find all numbers/percentages and their preceding comparison word
    for i, token in enumerate(doc):
        if token.like_num or token.ent_type_ in ("PERCENT", "CARDINAL"):
            # Look 2 words back to catch phrases like "above 75%"
            context_words = [doc[j].text.lower() for j in range(max(0, i-2), i)]
            matched_comp = None
            for cw in context_words:
                if cw in comparison_words:
                    matched_comp = cw
                    break
            
            if matched_comp:
                condition_str = f"{matched_comp} {token.text}"
                if matched_comp in ("before", "after"):
                    analysis["deadlines"].append(condition_str)
                else:
                    # Check if we already have this condition to avoid duplicates
                    if not any(token.text in c for c in analysis["conditions"]):
                        analysis["conditions"].append(condition_str)
            else:
                analysis["conditions"].append(token.text)

    # Merge detached percentage signs
    merged_conditions = []
    for c in analysis["conditions"]:
        if c == "%" and merged_conditions:
            merged_conditions[-1] += "%"
        else:
            merged_conditions.append(c)
    analysis["conditions"] = merged_conditions

    # Second pass: find standalone DATE/TIME entities
    for token in doc:
        if token.ent_type_ in ("DATE", "TIME"):
            if token.text not in [d.replace("before ", "").replace("after ", "") for d in analysis["deadlines"]]:
                analysis["deadlines"].append(token.text)

    # 5. Extract Subject, Action, Object
    for token in doc:
        if token.i >= exception_start_idx:
            continue
            
        if token.dep_ in ("nsubj", "nsubjpass"):
            analysis["subject"].append(token.text)
            
        if token.pos_ == "VERB" and token.dep_ == "ROOT":
            analysis["action"].append(token.lemma_)
            
        if token.dep_ in ("dobj", "pobj"):
            is_date = token.ent_type_ in ("DATE", "TIME")
            is_num = token.like_num or token.ent_type_ in ("PERCENT", "CARDINAL")
            
            if not is_date and not is_num:
                # Get the full noun phrase for the object
                for chunk in doc.noun_chunks:
                    if token in chunk:
                        analysis["object"].append(chunk.text)
                        break
                else:
                    analysis["object"].append(token.text)

    # Clean up lists
    for key in analysis:
        if isinstance(analysis[key], list):
            analysis[key] = list(dict.fromkeys(analysis[key])) 
            if not analysis[key]:
                analysis[key] = "None"

    return analysis