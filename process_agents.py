from crewai import Agent, Task, Crew, Process
from llm import get_llm
from tools import read_project_documents, calculate_payment_amount, check_required_documents, record_audit_event


def make_agents():
    llm = get_llm()
    return {
        'check_request': Agent(
            role='Check Request & BOQ Compliance Agent',
            goal='Validate that requested construction activities are traceable to the selected BOQ and identify missing evidence before execution.',
            backstory='You are a construction controls specialist. You never approve work. You prepare an evidence-based review for a human.',
            tools=[read_project_documents, check_required_documents, record_audit_event], llm=llm, verbose=False),
        'measurement': Agent(
            role='Measurement & Execution Readiness Agent',
            goal='Review requested quantities, units, previous approved quantities and supporting measurement evidence.',
            backstory='You are a quantity surveyor supporting a human consultant. Flag uncertainty instead of inventing quantities.',
            tools=[read_project_documents, calculate_payment_amount, record_audit_event], llm=llm, verbose=False),
        'document': Agent(
            role='Document & Evidence Agent',
            goal='Check that drawings, method statements, inspection records, invoices, photographs and other required documents are present and relevant.',
            backstory='You are a construction document controller. Missing evidence becomes an explicit exception.',
            tools=[read_project_documents, check_required_documents, record_audit_event], llm=llm, verbose=False),
        'ipc': Agent(
            role='IPC Preparation Agent',
            goal='Prepare an interim payment certificate only from work that has a human-approved check request and supplied measurement evidence.',
            backstory='You prepare payment quantities and calculations but have no authority to approve or release money.',
            tools=[read_project_documents, calculate_payment_amount, record_audit_event], llm=llm, verbose=False),
        'history': Agent(
            role='Historical & Audit Agent',
            goal='Compare the current request or IPC with previous stored records and flag duplicate, cumulative or inconsistent quantities.',
            backstory='You are an audit specialist focused on traceability and cumulative payment control.',
            tools=[record_audit_event], llm=llm, verbose=False),
        'review': Agent(
            role='Human Review Brief Agent',
            goal='Synthesize agent findings into a concise human decision brief with evidence, exceptions and recommended follow-up questions.',
            backstory='You support the decision-maker. You do not make the final decision.',
            tools=[record_audit_event], llm=llm, verbose=False),
    }


def run_check_request_review(context):
    a=make_agents()
    tasks=[
        Task(description=f"Review this check request against BOQ and project context. Identify BOQ traceability, scope mismatches and missing prerequisites. Context: {context}", expected_output='Structured findings with status PASS/EXCEPTION and evidence needed.', agent=a['check_request']),
        Task(description=f"Review quantities and measurement readiness for this proposed work. Do not approve. Context: {context}", expected_output='Quantity/measurement findings and exceptions.', agent=a['measurement']),
        Task(description=f"Check required documents for execution of the proposed work. Context: {context}", expected_output='Document checklist with present/missing/unclear items.', agent=a['document']),
        Task(description=f"Compare this request with previous records supplied in the context and flag duplicates or cumulative issues. Context: {context}", expected_output='Historical comparison findings.', agent=a['history']),
        Task(description='Create a human decision brief from the preceding findings. Clearly state that only a human can approve execution.', expected_output='Concise human approval brief.', agent=a['review'])
    ]
    return Crew(agents=list(a.values()), tasks=tasks, process=Process.sequential, verbose=False).kickoff()


def run_ipc_review(context):
    a=make_agents()
    tasks=[
        Task(description=f"Validate that every IPC line is linked to a human-approved check request and that the submitted quantity has measurement evidence. Context: {context}", expected_output='IPC eligibility findings.', agent=a['ipc']),
        Task(description=f"Check cumulative quantities and previous records for duplication or over-certification. Context: {context}", expected_output='Historical and cumulative findings.', agent=a['history']),
        Task(description=f"Check supporting documents for this IPC. Context: {context}", expected_output='IPC evidence findings.', agent=a['document']),
        Task(description='Create a human review brief. Never approve or release payment.', expected_output='Human IPC approval brief.', agent=a['review'])
    ]
    return Crew(agents=list(a.values()), tasks=tasks, process=Process.sequential, verbose=False).kickoff()
