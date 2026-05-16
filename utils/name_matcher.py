from difflib import SequenceMatcher

def normalize_name(name: str) -> str:
    return " ".join(name.lower().strip().split())

def name_match_percentage(name1: str, name2: str) -> float:
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    return SequenceMatcher(None, n1, n2).ratio() * 100
