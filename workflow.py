from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from crewai import Crew, Process, Task

from contract_agent import create_contract_agent
from intake_agent import create_intake_agent
from payment_agent import create_payment_agent
from review_agent import create_review_agent
from risk_agent import create_risk_agent
from valuation_agent import create_valuation_agent


@dataclass
class StageResult:
    key: str
    name: str
    result: str


def _run_stage(
    key: str,
    name: str,
    agent,
    description: str,
    status_callback: Callable[[str, str, int], None],
    progress: int,
) -> StageResult:
    status_callback(name, "Working", progress)

    task = Task(
        description=description,
        expected_output=(
            "Return a concise Markdown report. Clearly label VERIFIED FACTS, "
            "CALCULATIONS, ASSUMPTIONS, EXCEPTIONS, and HUMAN CHECKS where applicable. "
            "Never invent missing evidence."
        ),
        agent=agent,
        markdown=True,
    )

   crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        cache=True,
        respect_context_window=True,
    )
    output = crew.kickoff()
    status_callback(name, "Completed", progress)
    return StageResult(key=key, name=name, result=str(output.raw))


def run_payment_review(
    document_directory: str,
    project_context: str,
    status_callback: Callable[[str, str, int], None],
) -> list[StageResult]:
    results: list[StageResult] = []

    intake = _run_stage(
        "intake",
        "Intake & Evidence Agent",
        create_intake_agent(),
        f"""
You are the first stage of a construction payment review.

PROJECT CONTEXT:
{project_context}

DOCUMENT DIRECTORY:
{document_directory}

First use the Read project documents tool. Then create an evidence register:
- project/contract identifiers
- contractor/payee
- payment application/certificate number and period
- claimed gross value
- previous certified amount
- retention/deductions if stated
- schedule-of-values and key line items
- change orders/variations
- supporting records
- missing or unreadable information

Do not calculate or approve payment unless the source evidence supports it.
Use the Record audit event tool after completing your evidence extraction.
""",
        status_callback,
        10,
    )
    results.append(intake)

    contract = _run_stage(
        "contract",
        "Contract Compliance Agent",
        create_contract_agent(),
        f"""
Review the construction payment application using the original documents and the Intake report below.

PROJECT CONTEXT:
{project_context}

DOCUMENT DIRECTORY:
{document_directory}

INTAKE REPORT:
{intake.result}

First use the Read project documents tool to verify the source evidence. Identify:
- payment prerequisites
- retainage rules
- approved change-order requirements
- required declarations/certificates/waivers
- notice or timing requirements
- contractual deductions
- conflicts between the contract and the application

Do not decide whether the payment should be approved. State what is supported, missing, or requires human interpretation.
Use the Record audit event tool.
""",
        status_callback,
        25,
    )
    results.append(contract)

    valuation = _run_stage(
        "valuation",
        "Measurement & Valuation Agent",
        create_valuation_agent(),
        f"""
Validate quantities, rates and extensions for the payment application.

PROJECT CONTEXT:
{project_context}

DOCUMENT DIRECTORY:
{document_directory}

INTAKE REPORT:
{intake.result}

CONTRACT REPORT:
{contract.result}

First use the Read project documents tool. Compare schedule-of-values, claimed progress,
measurement/supporting records and approved changes where available.

Use the Calculate payment amount tool for arithmetic. Identify:
- arithmetic mismatches
- quantity/rate discrepancies
- unsupported progress claims
- change-order valuation issues
- items requiring human site/quantity verification

Never invent quantities or rates.
Use the Record audit event tool.
""",
        status_callback,
        40,
    )
    results.append(valuation)

    payment = _run_stage(
        "payment",
        "Payment Reconciliation Agent",
        create_payment_agent(),
        f"""
Reconcile the payment application.

PROJECT CONTEXT:
{project_context}

DOCUMENT DIRECTORY:
{document_directory}

INTAKE REPORT:
{intake.result}

CONTRACT REPORT:
{contract.result}

VALUATION REPORT:
{valuation.result}

First use the Read project documents tool.

Determine, only from supported evidence:
- gross earned/current value
- less previous certified amount
- retention
- other deductions
- resulting net payment position

Use the Calculate payment amount tool for all arithmetic. If an input is unknown,
say UNKNOWN rather than assuming zero unless the source explicitly supports zero.

This is an analysis only. Do not authorize or execute payment.
Use the Record audit event tool.
""",
        status_callback,
        55,
    )
    results.append(payment)

    risk = _run_stage(
        "risk",
        "Risk & Exceptions Agent",
        create_risk_agent(),
        f"""
Perform an independent controls review.

PROJECT CONTEXT:
{project_context}

DOCUMENT DIRECTORY:
{document_directory}

INTAKE:
{intake.result}

CONTRACT:
{contract.result}

VALUATION:
{valuation.result}

PAYMENT:
{payment.result}

First use the Read project documents tool. Use the Check required documents tool where useful.

Identify:
- missing required evidence
- conflicting figures
- duplicate or repeated billing indicators
- unsupported change orders
- unusual deductions or retention
- unresolved contract compliance issues
- items that require human/site verification
- any reason the automated analysis should not be relied upon without review

Do not label something fraudulent or non-compliant unless the evidence establishes that fact.
Use the Record audit event tool.
""",
        status_callback,
        70,
    )
    results.append(risk)

    review = _run_stage(
        "review",
        "Human Review Briefing Agent",
        create_review_agent(),
        f"""
Prepare the final human review brief.

PROJECT CONTEXT:
{project_context}

INTAKE:
{intake.result}

CONTRACT:
{contract.result}

VALUATION:
{valuation.result}

PAYMENT:
{payment.result}

RISK:
{risk.result}

First use the Read project documents tool if any source fact needs verification.

Produce:
1. Executive summary
2. Evidence-backed payment position
3. Key calculations
4. Exceptions and missing evidence
5. Human verification checklist
6. Suggested next administrative action, expressed only as a workflow step (for example,
   "human review required"), not as a payment approval or rejection

The human reviewer retains all decision authority. Never authorize, release, or execute payment.
Use the Record audit event tool.
""",
        status_callback,
        90,
    )
    results.append(review)

    status_callback("Human Decision Gate", "Waiting for human decision", 100)
    return results
