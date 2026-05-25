"""
SafeSpace — Counseling Data Ingestion Pipeline
Parses MHLCD.csv counseling dialogues and builds a FAISS vectorstore
for the trauma-informed RAG chatbot.
"""

import os
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


# --- Configuration ---
DATA_PATH = "data/MHLCD.csv"
DB_FAISS_PATH = "vectorstore/db_counseling"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def load_counseling_dialogues(csv_path: str) -> list[Document]:
    """
    Load MHLCD.csv and convert each dialogue into a LangChain Document.
    Groups utterances by dialogueId to reconstruct full conversations.
    """
    print(f"Loading counseling data from {csv_path}...")
    df = pd.read_csv(csv_path)

    # Clean up
    df["utteranceNo"] = pd.to_numeric(df["utteranceNo"], errors="coerce")
    df = df.dropna(subset=["utterances"])
    df = df.sort_values(["dialogueId", "utteranceNo"])

    documents = []
    grouped = df.groupby("dialogueId")

    for dialogue_id, group in grouped:
        # Build the conversation transcript
        lines = []
        for _, row in group.iterrows():
            role = str(row["authorRole"]).strip().capitalize()
            utterance = str(row["utterances"]).strip()
            lines.append(f"{role}: {utterance}")

        transcript = "\n".join(lines)

        # Extract metadata from counselor utterances
        counselor_rows = group[group["authorRole"] == "counselor"]
        avg_empathy = pd.to_numeric(counselor_rows["empathy"], errors="coerce").mean()
        strategies_used = (
            pd.to_numeric(counselor_rows["counselling-strategy"], errors="coerce")
            .dropna()
            .unique()
            .tolist()
        )

        # Create a structured document
        content = (
            f"--- Counseling Session (ID: {dialogue_id}) ---\n"
            f"{transcript}\n"
            f"--- End of Session ---"
        )

        metadata = {
            "dialogue_id": str(dialogue_id),
            "num_utterances": len(group),
            "avg_empathy_score": round(avg_empathy, 2) if pd.notna(avg_empathy) else 0.0,
            "counseling_strategies": str(strategies_used),
            "source": "MHLCD_counseling_dataset",
        }

        documents.append(Document(page_content=content, metadata=metadata))

    print(f"Loaded {len(documents)} counseling dialogues")
    return documents


def create_chunks(documents: list[Document]) -> list[Document]:
    """
    Split documents into chunks. Uses larger chunks to preserve
    conversation context and flow.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n--- End of Session ---", "\n\n", "\n", " "],
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} text chunks")
    return chunks


def build_vectorstore(chunks: list[Document], db_path: str):
    """
    Create embeddings and store in FAISS.
    """
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

    print("Building FAISS vectorstore (this may take a minute)...")
    db = FAISS.from_documents(chunks, embedding_model)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db.save_local(db_path)
    print(f"Vectorstore saved to {db_path}")
    return db


def main():
    print("=" * 60)
    print("  SafeSpace — Counseling Data Ingestion")
    print("=" * 60)

    # Step 1: Load dialogues
    documents = load_counseling_dialogues(DATA_PATH)

    # Step 2: Create chunks
    chunks = create_chunks(documents)

    # Step 3: Build and save vectorstore
    build_vectorstore(chunks, DB_FAISS_PATH)

    print("\nIngestion complete! Vectorstore ready for SafeSpace.")
    print(f"   Path: {DB_FAISS_PATH}")


if __name__ == "__main__":
    main()
