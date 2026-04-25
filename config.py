import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Configuration Constants
COLLECTION_NAME = "ucar_knowledge"
LLM_MODEL = "llama-3.1-8b-instant"
DATA_FOLDER = "./data"

UCAR_CONTEXT = """University Carthage (UCAR) is a Tunisian university with 32 institutions including:
ENIB, ENIM, ENISO, IPEIN, IPEIT, IPEST, INSAT, EPT,
ESSEC, IHEC, ISGB, ISGL, ISG, ISCAE, ESCT,
FSEGN, FSHST, FSB, FSES, FSHST, FLAH,
IPSI, ISBG, ISLT, ISPTK, ISTHS, IBLV,
INRST, ESA, and others under the Carthage umbrella."""
