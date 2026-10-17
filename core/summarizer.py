from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Split Transcript
# ---------------------------------------------------------------------------------------------------------------------------------

def split_transcript(transcript: str) -> list[str]:
    """Split a long transcript into overlapping text chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200,
    )

    return splitter.split_text(transcript)

# Summarize one chunk
# ---------------------------------------------------------------------------------------------------------------------------------

def summarize_chunk(chunk: str, llm) -> str:
    """Summarize one transcript chunk."""

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """Summarize this meeting transcript portion concisely.
            Preserve key discussions, decisions, action items, owners,
            deadlines, and important numbers.
            Do not invent or guess information."""
        ),
        ("human", "{text}")
    ])

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": chunk})


# Combine Summaries produces by each chunk 
# ---------------------------------------------------------------------------------------------------------------------------------

def combine_summaries(summaries: list[str], llm) -> str:
    """Combine partial summaries into one final summary."""
    
    combined = "\n\n".join(summaries)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """Combine the partial summaries into one professional
            meeting summary.

            Use appropriate headings and bullet points.
            Include the meeting overview, key discussions, decisions,
            action items with owners, deadlines, and next steps.
            Remove repetition without losing important details.
            Never invent information. Omit unsupported categories."""
        ),
        ("human", "{text}")
    ])

    chain = prompt | llm | StrOutputParser()

    return chain.invoke({"text": combined})

# Summarize the whole Transcript
# ---------------------------------------------------------------------------------------------------------------------------------

def summarize_transcript(transcript: str, llm) -> str:
    """Generate a meeting summary using map-reduce."""

    chunks = split_transcript(transcript)

    summaries = []

    for i, chunk in enumerate(chunks, start=1):
        print(f"Summarizing chunk {i}/{len(chunks)}...")
        summaries.append(summarize_chunk(chunk, llm))

    print("Generating final meeting summary...")

    return combine_summaries(summaries, llm)


# Generate Meeting Title
# ---------------------------------------------------------------------------------------------------------------------------------

def generate_title(transcript: str, llm) -> str:
    """Generate a professional meeting title of at most eight words."""

    title_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            Generate a short, professional title for this meeting.
            Requirements:
            - Maximum 8 words
            - Reflect the main topic
            - Do not use quotation marks
            - Return only the title
            """,
        ),
        ("human", "{text}"),
    ])

    title_chain = title_prompt | llm | StrOutputParser()

    return title_chain.invoke({"text": transcript[:2000]}).strip()
