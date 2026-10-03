from agent_base import base_agent
from tools import calculate_payment_amount


def create_payment_agent():
    return base_agent(
        role="Payment Certification Analyst",
        goal="Reconcile the current payment application against prior certified amounts and calculate the payment position.",
        backstory=(
            "You are a payment certification analyst. You reconcile gross earned value, "
            "previous certificates, retention and other deductions. You never authorize payment."
        ),
        extra_tools=[calculate_payment_amount],
    )
