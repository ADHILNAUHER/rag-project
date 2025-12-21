import os
import tempfile
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore

from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")


def _get_embeddings_model() -> HuggingFaceEndpointEmbeddings:
    """
    Lazily initializes and returns the HuggingFace embeddings client.
    This function is called *after* load_dotenv() has run.
    """
    if not HUGGINGFACEHUB_API_TOKEN:
        raise ValueError("HUGGINGFACEHUB_API_TOKEN is not set. Check your .env file.")

    return HuggingFaceEndpointEmbeddings(model="sentence-transformers/all-MiniLM-L6-v2")


def _get_pinecone_client() -> Pinecone:
    """
    Lazily initializes and returns the Pinecone client.
    This function is called *after* load_dotenv() has run.
    """
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY is not set. Check your .env file.")

    pc = Pinecone(api_key=PINECONE_API_KEY)

    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating new Pinecone index: {PINECONE_INDEX_NAME}")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=384,  # dimension of all-MiniLM-L6-v2
            metric="dotproduct",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc


def _get_vectorstore() -> PineconeVectorStore:
    """
    Initializes the PineconeVectorStore using the lazy client.
    """
    pc = _get_pinecone_client()
    index = pc.Index(PINECONE_INDEX_NAME)

    embeddings = _get_embeddings_model()

    vectorstore = PineconeVectorStore(
        index=index,
        embedding=embeddings,
        text_key="text",
    )
    return vectorstore


def get_document_loader(filename: str, file_path: str):
    """Selects the appropriate document loader based on the file extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        return PyPDFLoader(file_path)
    elif ext == ".txt":
        return TextLoader(file_path)
    elif ext == ".docx":
        return Docx2txtLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


async def ingest_document(file_content: bytes, file_id: str, filename: str):
    """
    Loads (from bytes), splits, and ingests a document's vectors into Pinecone.
    """
    print(f"Starting ingestion for file_id: {file_id}, filename: {filename}")
    tmp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f"_{filename}"
        ) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        print(f"File content written to temporary file: {tmp_file_path}")

        loader = get_document_loader(filename, tmp_file_path)
        documents = loader.load()

        if not documents:
            print("No documents loaded, skipping text splitting.")
            return

        print(f"Loaded {len(documents)} document(s) from file.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split document into {len(chunks)} chunks.")

        if not chunks:
            print("No chunks to ingest.")
            return

        for chunk in chunks:
            chunk.metadata["file_id"] = file_id
            chunk.metadata["filename"] = filename

        print(f"Added metadata (file_id: {file_id}) to all chunks.")

        vectorstore = _get_vectorstore()
        await vectorstore.aadd_documents(chunks)

        print(
            f"Successfully ingested {len(chunks)} chunks into Pinecone for file_id: {file_id}"
        )

    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
            print(f"Cleaned up temporary file: {tmp_file_path}")


async def delete_vectors(file_id: str):
    """
    Deletes all vectors associated with a specific file_id from Pinecone.
    """
    print(f"Attempting to delete vectors for file_id: {file_id}")
    try:
        vectorstore = _get_vectorstore()
        await vectorstore.adelete(filter={"file_id": file_id})
        print(f"Successfully deleted vectors for file_id: {file_id}")
    except Exception as e:
        print(f"Error deleting vectors: {e}")
        raise
