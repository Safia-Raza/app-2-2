from agent_base import base_agent
from tools import check_required_documents


def create_risk_agent():
    return base_agent(
        role="Payment Risk and Exceptions Analyst",
        goal="Find discrepancies, missing evidence, duplicate billing indicators, unusual movements and unresolved exceptions.",
        backstory=(
            "You are an independent controls analyst. You challenge unsupported conclusions, "
            "separate facts from risks, and identify what a human reviewer must verify."
        ),
        extra_tools=[check_required_documents],
    )
