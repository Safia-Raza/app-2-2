import os
from crewai import LLM


def get_llm():
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        raise RuntimeError('GROQ_API_KEY is not configured. Add it to Streamlit Secrets.')
    
    # Using the standard working model name for Groq
    return LLM(
        model='groq/llama-3.3-70b-versatile',
        api_key=api_key,
        temperature=0.1
    )
