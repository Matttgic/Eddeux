# utils.py

def normalize_name(name: str) -> str:
    """Normalise un nom de joueur au format 'N. Djokovic'"""
    parts = name.strip().split()
    if len(parts) == 1:
        return name
    return f"{parts[0][0]}. {' '.join(parts[1:])}"
