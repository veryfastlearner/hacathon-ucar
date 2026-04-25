import re

class Normalizer:
    
    @staticmethod
    def normalize_date_french(raw_date: str) -> str:
        """Converts things like '16 Mars 2026' to '2026-03-16'"""
        if not raw_date: return None
        months = {
            "janvier": "01", "février": "02", "fevrier": "02", "mars": "03",
            "avril": "04", "mai": "05", "juin": "06", "juillet": "07",
            "août": "08", "aout": "08", "septembre": "09", "octobre": "10",
            "novembre": "11", "décembre": "12", "decembre": "12"
        }
        raw_lower = str(raw_date).lower().strip()
        parts = raw_lower.split()
        if len(parts) >= 3:
            day = parts[0].zfill(2)
            month_str = parts[1]
            year = parts[2]
            month = months.get(month_str, "01")
            return f"{year}-{month}-{day}"
        return raw_date

    @staticmethod
    def normalize_percentage(raw_val: str) -> float:
        """Converts '72,5 %' to 72.5"""
        if not raw_val: return 0.0
        val = str(raw_val).replace(" ","").replace("%","").replace(",",".")
        try:
            return float(val)
        except ValueError:
            return 0.0

    @staticmethod
    def normalize_currency(raw_val: str) -> float:
        """Converts '2.100.000 TND' to 2100000"""
        if not raw_val: return 0.0
        val = str(raw_val).lower().replace("tnd","").replace("dt","").replace(" ","").replace(".","").strip()
        try:
            return float(val)
        except ValueError:
            return 0.0
