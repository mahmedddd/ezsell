import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from core.fraud_protection import FraudProtectionService

def test_quality_detection():
    test_cases = [
        ("kenneknvlkenvleknvleknvelvnlknvlkfvnflkvnsvnls", True, "User example (long word)"),
        ("vnlknvlkfv", True, "Unpronounceable word"),
        ("k8#f2!m9*zL1^qPd7!xQ2$wR9*bN4@mV1#pL9^zK", True, "High entropy gibberish"),
        ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", True, "Low diversity repetition"),
        ("This is a high quality iPhone 7 Plus in great condition.", False, "Normal English"),
        ("Ye phone bilkul naya hai aur condition bohot achi hai.", False, "Normal Roman Urdu"),
        ("Urgent sale! MacBook Pro M1 2020 8/256GB with original charger.", False, "Normal Listing Desc"),
        ("!!!!!!!!!", True, "Excessive punctuation/repetition"),
    ]
    
    with open("quality_results.txt", "w") as f:
        f.write(f"{'Text Snippet':<30} | {'Expected':<8} | {'Result':<8} | {'Reason':<20}\n")
        f.write("-" * 80 + "\n")
        
        for text, expected_nonsense, label in test_cases:
            is_nonsense, reason = FraudProtectionService.is_nonsense(text)
            status = "PASS" if is_nonsense == expected_nonsense else "FAIL"
            snippet = (text[:27] + '..') if len(text) > 27 else text
            f.write(f"{snippet:<30} | {str(expected_nonsense):<8} | {str(is_nonsense):<8} | {reason:<20}\n")

if __name__ == "__main__":
    test_quality_detection()
