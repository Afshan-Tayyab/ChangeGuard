# backend/services/change_detector.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from services.semantic_analyzer import analyze_sentence

def calculate_similarity(text1: str, text2: str) -> float:
    vectorizer = TfidfVectorizer()
    try:
        tfidf = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    except ValueError:
        return 0.0

def fmt(val):
    if val == "None" or val is None: 
        return "None"
    if isinstance(val, list): 
        return " ".join(str(v) for v in val) # Changed to space-join for clean UI
    return str(val)

def detect_changes(old_analysis: dict, new_analysis: dict) -> list:
    changes = []
    condition_changed = False
    
    # 1. Modality Change
    if old_analysis["modality"] != new_analysis["modality"]:
        changes.append({
            "type": "Modality Change",
            "old": fmt(old_analysis["modality"]),
            "new": fmt(new_analysis["modality"]),
            "impact": "Permission changed into an obligation (or vice versa)."
        })
        
    # 2. Deadline Change
    if old_analysis["deadlines"] != new_analysis["deadlines"]:
        changes.append({
            "type": "Deadline Change",
            "old": fmt(old_analysis["deadlines"]),
            "new": fmt(new_analysis["deadlines"]),
            "impact": f"The deadline or temporal condition changed from {fmt(old_analysis['deadlines'])} to {fmt(new_analysis['deadlines'])}."
        })

    # 3. Negation Change
    if old_analysis["negation"] != new_analysis["negation"]:
        status = "Negation Added" if new_analysis["negation"] else "Negation Removed"
        impact = "Permission has been removed. The action is now prohibited." if new_analysis["negation"] else "The restriction has been lifted. The action is now permitted."
        changes.append({
            "type": status,
            "old": str(old_analysis["negation"]),
            "new": str(new_analysis["negation"]),
            "impact": impact
        })
        
    # 4. Condition Change
    if old_analysis["conditions"] != new_analysis["conditions"]:
        condition_changed = True
        
        old_cond = fmt(old_analysis["conditions"])
        new_cond = fmt(new_analysis["conditions"])
        
        # Clean up any duplicate formatting
        old_cond = old_cond.replace("above above", "above").replace("least least", "least")
        new_cond = new_cond.replace("above above", "above").replace("least least", "least")

        changes.append({
            "type": "Condition Change",
            "old": old_cond,
            "new": new_cond,
            "impact": f"The requirement changed from {old_cond} to {new_cond}."
        })
        
    # 5. Restriction Change
    if old_analysis["restrictions"] != new_analysis["restrictions"]:
        changes.append({
            "type": "Restriction Change",
            "old": fmt(old_analysis["restrictions"]),
            "new": fmt(new_analysis["restrictions"]),
            "impact": f"Eligibility changed from '{fmt(old_analysis['restrictions'])}' to '{fmt(new_analysis['restrictions'])}'."
        })

    # 6. Exception Change
    if old_analysis["exceptions"] != new_analysis["exceptions"]:
        status = "Exception Added" if old_analysis["exceptions"] == "None" else "Exception Changed"
        changes.append({
            "type": status,
            "old": fmt(old_analysis["exceptions"]),
            "new": fmt(new_analysis["exceptions"]),
            "impact": "A special exemption or condition was added/modified."
        })
        
    # 7. Object Change
    if not condition_changed and old_analysis["object"] != new_analysis["object"]:
        changes.append({
            "type": "Object Change",
            "old": fmt(old_analysis["object"]),
            "new": fmt(new_analysis["object"]),
            "impact": f"The target of the action changed from {fmt(old_analysis['object'])} to {fmt(new_analysis['object'])}."
        })

    return changes

def compare_documents(old_sentences: list, new_sentences: list) -> list:
    comparison_results = []
    used_new_indices = set()

    for i, old_sent in enumerate(old_sentences):
        old_analysis = analyze_sentence(old_sent)
        best_match_idx = -1
        best_similarity = 0.0
        action_match = False
        
        for j, new_sent in enumerate(new_sentences):
            if j in used_new_indices:
                continue
            
            sim = calculate_similarity(old_sent, new_sent)
            new_analysis = analyze_sentence(new_sent)
            
            current_action_match = (old_analysis["action"] != "None" and old_analysis["action"] == new_analysis["action"])
            
            if sim > best_similarity or (current_action_match and sim > 0.15):
                best_similarity = sim
                best_match_idx = j
                action_match = current_action_match
                
        if (best_similarity > 0.3 or action_match) and best_match_idx != -1:
            used_new_indices.add(best_match_idx)
            new_sent = new_sentences[best_match_idx]
            new_analysis = analyze_sentence(new_sent)
            
            changes = detect_changes(old_analysis, new_analysis)
            
            if changes:
                comparison_results.append({
                    "status": "Modified",
                    "old_sentence": old_sent,
                    "new_sentence": new_sent,
                    "changes_detected": changes
                })
            else:
                comparison_results.append({
                    "status": "Unchanged",
                    "old_sentence": old_sent,
                    "new_sentence": new_sent,
                    "changes_detected": []
                })
                
        else:
            comparison_results.append({
                "status": "Deleted",
                "old_sentence": old_sent,
                "new_sentence": None,
                "changes_detected": []
            })

    for j, new_sent in enumerate(new_sentences):
        if j not in used_new_indices:
            comparison_results.append({
                "status": "Added",
                "old_sentence": None,
                "new_sentence": new_sent,
                "changes_detected": []
            })

    return comparison_results