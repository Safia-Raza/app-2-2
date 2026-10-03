# BuildPay AI

Multi-agent construction payment workflow using CrewAI + Groq + Streamlit.

## Workflow

1. Contractor selects the double-storey house BOQ and creates a Check Request against BOQ activities.
2. Contractor uploads necessary supporting documents.
3. AI agents review BOQ traceability, measurement readiness, evidence and historical records.
4. Human approves/rejects/returns the Check Request.
5. Only human-approved Check Requests can generate an IPC.
6. Consultant enters executed quantities and rate; the IPC preparation agents validate the package.
7. Human approves/returns the IPC.
8. Check Requests, IPCs and audit events are stored in SQLite.

## Human-in-the-loop rule

Agents never approve work, certify payment, or release funds. They prepare evidence and findings only.

## Streamlit Cloud

- Main file: `app.py`
- Python: 3.12
- Add `GROQ_API_KEY` in Streamlit Secrets.
- `requirements.txt` pins the tested dependency family.

## Persistence

The demo uses `buildpay_history.db` (SQLite). For production, replace this with a managed database such as PostgreSQL so history is durable across infrastructure replacement and multiple app instances.
