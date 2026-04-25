import os
import fitz  # PyMuPDF
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

# Initialize Local Qdrant (This creates a folder on your disk)
client = QdrantClient(path="./qdrant_db")
COLLECTION_NAME = "ucar_knowledge"

def run_ingestion():
    # 1. Prepare Collection
    # Note: FastEmbed uses 384-dim vectors by default
    docs = []
    metadata = []
    data_folder = "./data"

    if not os.path.exists(data_folder):
        print(f"Error: Create a folder named {data_folder} and put your PDFs there!")
        return

    # 2. Extract text from PDFs
    for filename in os.listdir(data_folder):
        if filename.endswith(".pdf"):
            print(f"📄 Processing: {filename}")
            doc = fitz.open(os.path.join(data_folder, filename))
            for page_num, page in enumerate(doc):
                text = page.get_text().strip()
                if len(text) > 50:  # Skip empty pages
                    docs.append(text)
                    metadata.append({
                        "source": filename,
                        "page": page_num + 1,
                        "institution": "ENICAR" if "eni" in filename.lower() else "UCAR"
                    })

    # 3. Add to Qdrant (This handles embedding internally for free)
    print("⏳ Generating embeddings and saving to disk...")
    client.add(
        collection_name=COLLECTION_NAME,
        documents=docs,
        metadata=metadata
    )
    print(f"✅ Success! Data saved in ./qdrant_db")

if __name__ == "__main__":
    run_ingestion()