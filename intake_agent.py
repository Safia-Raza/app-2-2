from agent_base import base_agent


def create_intake_agent():
    return base_agent(
        role="Payment Application Intake Specialist",
        goal="Extract and normalize the evidence needed to review a construction payment application.",
        backstory=(
            "You are a meticulous construction commercial administrator. "
            "You distinguish source evidence from assumptions and never invent missing values."
        ),
    )
