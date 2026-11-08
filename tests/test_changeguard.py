# tests/test_changeguard.py
import sys
import os

# Get the absolute path of the main ChangeGuard folder and add backend to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, 'backend'))

from services.semantic_analyzer import analyze_sentence
from services.change_detector import detect_changes, compare_documents

def run_test(test_num, name, old_text, new_text, expected_category):
    print(f"Test {test_num}: {name}")
    old_analysis = analyze_sentence(old_text)
    new_analysis = analyze_sentence(new_text)
    changes = detect_changes(old_analysis, new_analysis)
    
    found = False
    for change in changes:
        if expected_category in change["type"]:
            found = True
            print(f"  [PASS] Detected: {change['type']}")
            print(f"         Old: {change['old']} | New: {change['new']}")
            break
            
    if not found:
        print(f"  [FAIL] Expected '{expected_category}'. Found: {[c['type'] for c in changes]}")
    print("-" * 40)

if __name__ == "__main__":
    print("=== CHANGEGUARD NLP TEST SUITE ===\n")
    
    run_test(1, "Modality Change", "Students may apply.", "Students must apply.", "Modality Change")
    run_test(2, "Deadline Change", "Submit by Friday.", "Submit by Monday.", "Deadline Change")
    run_test(3, "Negation Added", "Students are allowed.", "Students are not allowed.", "Negation Added")
    run_test(4, "Negation Removed", "Students are not allowed.", "Students are allowed.", "Negation Removed")
    run_test(5, "Condition Change", "Attendance above 75%.", "Attendance above 85%.", "Condition Change")
    run_test(6, "Restriction Change", "All students may participate.", "Only final-year students may participate.", "Restriction Change")
    run_test(7, "Exception Added", "Students must pay the fee.", "Students must pay the fee unless they have a scholarship.", "Exception Added")
    
    # Test 8 uses full sentences so spaCy can correctly identify the object
    run_test(8, "Object Change", "Students must submit applications.", "Students must submit certificates.", "Object Change")

    # Test Unchanged
    print("Test 9: Unchanged Sentence")
    old_s = ["Only final-year students are eligible."]
    new_s = ["Only final-year students are eligible."]
    res = compare_documents(old_s, new_s)
    if res[0]["status"] == "Unchanged":
        print("  [PASS] Status is Unchanged")
    else:
        print(f"  [FAIL] Status was {res[0]['status']}")
    print("-" * 40)