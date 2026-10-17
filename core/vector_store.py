import os 
from langchain_chroma import Chroma 
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Configuration for Vector Store
# ---------------------------------------------------------------------------------------------------------------------------------

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"
EMBEDDING_MODEL  = "all-MiniLM-L6-v2"

# Function to get embeddings
# ---------------------------------------------------------------------------------------------------------------------------------

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name = EMBEDDING_MODEL,
        model_kwargs = {"device" : 'cpu'}
    )

# Function to build vector store from transcript
# ---------------------------------------------------------------------------------------------------------------------------------

def build_vector_store(transcript: str, video_id: str, video_title: str, session_id: str) -> Chroma:
    """Add a video's transcript chunks to the shared Chroma database."""

    if not transcript or not transcript.strip():
        raise ValueError("Transcript cannot be empty.")

    if not video_id or not video_id.strip():
        raise ValueError("Video ID cannot be empty.")

    if not video_title or not video_title.strip():
        raise ValueError("Video title cannot be empty.")

    if not session_id or not session_id.strip():
        raise ValueError("Session ID cannot be empty.")

    print(f"Indexing video: {video_title}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(transcript)

    documents = [
        Document(page_content=chunk, 
            metadata={
                "video_id": video_id,
                "video_title": video_title,
                "session_id": session_id,
                "chunk_index": i,
            },
        )
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()

    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )

    # Use deterministic IDs so re-indexing replaces the same video's chunks.
    chunk_ids = [
        f"{session_id}:{video_id}:{i}"
        for i in range(len(documents))
    ]

    # Remove old chunks for this video in this session.
    vector_store.delete(
        where={
            "$and": [
                {"session_id": session_id},
                {"video_id": video_id},
            ]
        }
    )

    vector_store.add_documents(
        documents=documents,
        ids=chunk_ids,
    )

    return vector_store

# Function to load vector store
# ---------------------------------------------------------------------------------------------------------------------------------

def load_vector_store() ->Chroma:
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function= embeddings,
        persist_directory=CHROMA_DIR
    )

    return vector_store

# Function to get retriever from vector store
# ---------------------------------------------------------------------------------------------------------------------------------

def get_retriever(vector_store: Chroma, k: int = 4, session_id: str | None = None, video_id: str | None = None):
    """Create a retriever with optional session and video filters."""

    search_kwargs = {"k": k}
    filters = []

    if session_id is not None:
        filters.append({"session_id": session_id})

    if video_id is not None:
        filters.append({"video_id": video_id})

    if len(filters) == 1:
        search_kwargs["filter"] = filters[0]
    elif len(filters) > 1:
        search_kwargs["filter"] = {"$and": filters}

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )