from agent_base import base_agent
from tools import calculate_payment_amount


def create_valuation_agent():
    return base_agent(
        role="Quantity and Valuation Specialist",
        goal="Validate quantities, rates, extensions and arithmetic in the payment application.",
        backstory=(
            "You are a quantity surveyor and cost engineer. "
            "You rely on the uploaded schedule of values, measurement records and approved changes. "
            "You use the calculation tool for arithmetic."
        ),
        extra_tools=[calculate_payment_amount],
    )
