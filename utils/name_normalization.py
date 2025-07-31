# utils/name_normalization.py
import re
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class NameNormalizer:
    """Advanced name normalization for tennis players"""
    
    # Common name variations and corrections
    NAME_CORRECTIONS = {
        "De Minaur A.": "de Minaur A.",
        "Van De Zandschulp B.": "van de Zandschulp B.",
        "Del Potro J.": "del Potro J.",
        "Da Silva J.": "da Silva J.",
    }
    
    # Special character handling
    ACCENT_MAP = {
        'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a', 'ā': 'a', 'ã': 'a',
        'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e', 'ē': 'e',
        'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i', 'ī': 'i',
        'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o', 'ō': 'o', 'õ': 'o',
        'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u', 'ū': 'u',
        'ñ': 'n', 'ç': 'c', 'ß': 'ss',
        'Á': 'A', 'À': 'A', 'Ä': 'A', 'Â': 'A', 'Ā': 'A', 'Ã': 'A',
        'É': 'E', 'È': 'E', 'Ë': 'E', 'Ê': 'E', 'Ē': 'E',
        'Í': 'I', 'Ì': 'I', 'Ï': 'I', 'Î': 'I', 'Ī': 'I',
        'Ó': 'O', 'Ò': 'O', 'Ö': 'O', 'Ô': 'O', 'Ō': 'O', 'Õ': 'O',
        'Ú': 'U', 'Ù': 'U', 'Ü': 'U', 'Û': 'U', 'Ū': 'U',
        'Ñ': 'N', 'Ç': 'C'
    }
    
    @classmethod
    def remove_accents(cls, text: str) -> str:
        """Remove accents from text"""
        for accented, plain in cls.ACCENT_MAP.items():
            text = text.replace(accented, plain)
        return text
    
    @classmethod
    def normalize_excel_format(cls, full_name: str) -> str:
        """Convert full name to Excel format (Last First.)"""
        if not full_name or not full_name.strip():
            return ""
            
        name = cls.remove_accents(full_name.strip())
        parts = name.split()
        
        if len(parts) < 2:
            return name
            
        first = parts[0]
        last = " ".join(parts[1:])
        normalized = f"{last} {first[0]}."
        
        # Apply corrections
        return cls.NAME_CORRECTIONS.get(normalized, normalized)
    
    @classmethod
    def normalize_api_format(cls, full_name: str) -> str:
        """Convert API name to standard format (First Last)"""
        if not full_name or not full_name.strip():
            return ""
            
        name = cls.remove_accents(full_name.strip())
        
        # Handle various API formats
        if "." in name:
            # Format: "Last F." -> "F Last"
            parts = name.split()
            if len(parts) >= 2 and parts[-1].endswith('.'):
                first_initial = parts[-1][0]
                last = " ".join(parts[:-1])
                return f"{first_initial}. {last}"
        
        return name
    
    @classmethod
    def fuzzy_match_score(cls, name1: str, name2: str) -> float:
        """Calculate fuzzy matching score between two names"""
        name1_clean = cls.remove_accents(name1).lower().replace(".", "")
        name2_clean = cls.remove_accents(name2).lower().replace(".", "")
        
        # Exact match
        if name1_clean == name2_clean:
            return 1.0
        
        # Check if one is contained in the other
        if name1_clean in name2_clean or name2_clean in name1_clean:
            return 0.8
        
        # Check for partial matches (last name)
        parts1 = name1_clean.split()
        parts2 = name2_clean.split()
        
        if len(parts1) >= 2 and len(parts2) >= 2:
            # Compare last names
            if parts1[-1] == parts2[-1]:
                return 0.7
        
        return 0.0