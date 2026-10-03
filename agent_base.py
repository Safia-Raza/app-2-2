from crewai import Agent
from llm import get_llm
from tools import read_project_documents, record_audit_event


def base_agent(role: str, goal: str, backstory: str, extra_tools=None) -> Agent:
    tools = [read_project_documents, record_audit_event]
    if extra_tools:
        tools.extend(extra_tools)

    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        llm=get_llm(),
        tools=tools,
        allow_delegation=False,
        verbose=False,
        max_iter=8,
        max_retry_limit=2,
        respect_context_window=True,
    )
