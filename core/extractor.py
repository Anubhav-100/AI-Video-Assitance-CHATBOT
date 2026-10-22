#Actionableitems , decision , questions 

import os 
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from schemas.analysis import SummarizeRequest


# Build LLM Chain
# ---------------------------------------------------------------------------------------------------------------------------------

def build_chain(system_prompt: str, llm):
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{text}"),
    ])

    return prompt | llm | StrOutputParser()


# Extract Action Items
# ---------------------------------------------------------------------------------------------------------------------------------

def extract_action_items(transcript:str, llm)->str:
    transcript = SummarizeRequest(transcript=transcript).transcript
    action_prompt = """You are an expert meeting analyst. From the meeting transcript, "
        "extract all action items. For each provide:\n"
        "- Task description\n"
        "- Owner (who is responsible)\n"
        "- Deadline (if mentioned, else write 'Not specified')\n\n"
        "Format as a numbered list. If none found say 'No action items found.'""" 
    chain = build_chain(action_prompt, llm)

    return chain.invoke(transcript)

# Extract Key Decisions
# ---------------------------------------------------------------------------------------------------------------------------------

def extract_key_decisions(transcript: str, llm) -> str:
    transcript = SummarizeRequest(transcript=transcript).transcript
    key_decision_prompt = """You are an expert meeting analyst. From the meeting transcript, "
        "extract all key decisions made. Format as a numbered list. "
        "If none found say 'No key decisions found.'"""
    chain = build_chain(key_decision_prompt, llm)

    return chain.invoke(transcript)


# Extract Open Questions
# ---------------------------------------------------------------------------------------------------------------------------------

def extract_questions(transcript: str, llm) -> str:
    transcript = SummarizeRequest(transcript=transcript).transcript
    questions_prompt = """You are an expert meeting analyst. From the meeting transcript, extract all unresolved questions "
        "or topics needing follow-up. Format as a numbered list. "
        "If none found say 'No open questions found.'"""
    chain = build_chain(questions_prompt, llm)

    return chain.invoke(transcript)