import re

MAP = {
    "université de carthage": "UCAR",
    "ucar": "UCAR",
    "faculté des sciences juridiques, politiques et sociales de tunis": "UCAR_FSJPST",
    "fsjpst": "UCAR_FSJPST",
    "ecole nationale des sciences et technologies avancées de borj cédria": "UCAR_ENSTAB",
    "enstab": "UCAR_ENSTAB",
    "ecole nationale d'architecture et d'urbanisme de tunis": "UCAR_ENAU",
    "enau": "UCAR_ENAU"
}

def get_institution_id(raw_name: str) -> str:
    """Uses fuzzy logic to return the mapped institution ID, or a fallback."""
    if not str(raw_name).strip():
        return "UNKNOWN_INSTITUTION"
    raw = str(raw_name).strip().lower()
    
    # Direct match
    if raw in MAP:
        return MAP[raw]
    
    # Partial matching
    for key, val in MAP.items():
        if key in raw or raw in key:
            return val
            
    # Fallback if no exact keys but looks like UCAR
    if "carthage" in raw:
        return "UCAR"
        
    return "UNKNOWN_INSTITUTION"
