import io, json, os, hashlib
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st

from storage import init_db, next_number, create_check_request, update_check_request, list_check_requests, get_check_request, create_ipc, update_ipc, list_ipcs
from process_agents import run_check_request_review, run_ipc_review

init_db()
UPLOAD_ROOT = Path(__file__).resolve().parent / 'uploaded_documents'
UPLOAD_ROOT.mkdir(exist_ok=True)

def save_uploaded_files(files, record_id):
    folder = UPLOAD_ROOT / record_id
    folder.mkdir(parents=True, exist_ok=True)
    saved=[]
    for f in files or []:
        safe = Path(f.name).name
        target = folder / safe
        target.write_bytes(f.getbuffer())
        saved.append(str(target))
    return saved


st.set_page_config(page_title='BuildPay AI | Construction Payment Workforce', page_icon='🏗️', layout='wide', initial_sidebar_state='expanded')

st.markdown('''<style>
.block-container{padding-top:1.2rem;max-width:1450px}.hero{padding:28px 30px;border-radius:24px;background:linear-gradient(135deg,#111827,#1f2937);color:white;margin-bottom:20px}.hero h1{font-size:2.2rem;margin:0}.hero p{color:#cbd5e1;margin:.5rem 0 0}.pill{display:inline-block;padding:6px 12px;border-radius:999px;background:#e5f5e9;color:#166534;font-weight:700;font-size:.8rem;margin-right:6px}.agentbox{padding:14px;border:1px solid #e5e7eb;border-radius:16px;background:#fafafa}.danger{padding:14px;border-radius:14px;background:#fff7ed;border:1px solid #fed7aa}.human{padding:18px;border-radius:18px;background:#eff6ff;border:1px solid #bfdbfe}.stTabs [data-baseweb="tab"]{font-weight:700}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🏗️ BuildPay AI</h1><p>Construction payment workforce — BOQ control → Check Request → Human approval → Execution → IPC → Human approval → Historical record.</p><span class="pill">AI assists</span><span class="pill">Human decides</span><span class="pill">No autonomous payment</span></div>', unsafe_allow_html=True)

if 'active_agent' not in st.session_state: st.session_state.active_agent='Ready'

with st.sidebar:
    st.subheader('Project')
    project=st.text_input('Project name', 'Double Storey Residential House')
    house_type=st.selectbox('House type', ['5 Marla','10 Marla','1 Kanal'])
    contractor=st.text_input('Contractor', 'Contractor A')
    consultant=st.text_input('Consultant', 'Consultant A')
    client=st.text_input('Client', 'Client A')
    st.divider()
    st.metric('Check Requests', len(list_check_requests(project)))
    st.metric('IPCs', len(list_ipcs(project)))
    st.caption(f'Current agent: {st.session_state.active_agent}')

contractor_tab, consultant_tab, client_tab, records_tab = st.tabs(['🏗️ Contractor','📐 Consultant','🏢 Client','🗂️ Records & Audit'])

BOQ_MAP={'5 Marla':'boq_templates/5_marla_double_storey_civil_boq.xlsx','10 Marla':'boq_templates/10_marla_double_storey_civil_boq.xlsx','1 Kanal':'boq_templates/1_kanal_double_storey_civil_boq.xlsx'}

with contractor_tab:
    st.header('Contractor Workspace')
    st.caption('Create a Check Request against approved BOQ activities and upload execution evidence.')
    st.download_button('⬇️ Download selected BOQ', open(BOQ_MAP[house_type],'rb').read(), file_name=os.path.basename(BOQ_MAP[house_type]), mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    with st.form('cr_form'):
        activity=st.selectbox('BOQ activity', ['Mobilization','Grey Structure Works','Finishing Works'])
        description=st.text_area('Work proposed for execution', placeholder='e.g. Block masonry for ground-floor external walls as per drawings and BOQ.')
        requested_qty=st.number_input('Requested quantity', min_value=0.0, step=0.01)
        unit=st.text_input('Unit', 'm2')
        boq_items=st.text_input('BOQ item codes / references', placeholder='e.g. GS-04, GS-05')
        docs=st.file_uploader('Necessary documents', type=['pdf','docx','xlsx','xls','csv','txt','jpg','jpeg','png'], accept_multiple_files=True, key='cr_docs')
        submitted=st.form_submit_button('📨 Generate Check Request', type='primary', use_container_width=True)
    if submitted:
        request_no=next_number('CR','check_requests','request_no')
        document_names=[d.name for d in docs] if docs else []
        saved_paths=save_uploaded_files(docs, request_no)
        data={'request_no':request_no,'project':project,'house_type':house_type,'activity':activity,'boq_items':[x.strip() for x in boq_items.split(',') if x.strip()],'description':description,'requested_qty':requested_qty,'unit':unit,'contractor':contractor,'consultant':consultant,'client':client,'documents':document_names,'document_paths':saved_paths,'actor':contractor}
        create_check_request(data)
        st.session_state.active_agent='Check Request & BOQ Compliance Agent'
        context=json.dumps(data, indent=2)
        with st.status('AI workforce reviewing the Check Request…', expanded=True) as status:
            st.write('🔵 Check Request & BOQ Compliance Agent — working')
            result=run_check_request_review(context)
            st.write('🟢 Measurement & Execution Readiness Agent — complete')
            st.write('🟢 Document & Evidence Agent — complete')
            st.write('🟢 Historical & Audit Agent — complete')
            st.write('🟢 Human Review Brief Agent — complete')
            status.update(label='AI review completed — waiting for human decision', state='complete')
        update_check_request(request_no, status='AWAITING_HUMAN_APPROVAL', ai_review={'crew_output':str(result)}, actor='AI Workforce')
        st.success(f'Check Request {request_no} generated and sent to human approval.')
        st.session_state.active_agent='Waiting for Human Approval'

with consultant_tab:
    st.header('Consultant Workspace')
    st.caption('Review evidence, measurement and AI findings. Approval remains a human action.')
    rows=list_check_requests(project)
    if rows:
        options=[r['request_no'] for r in rows]
        selected=st.selectbox('Check Request', options)
        r=get_check_request(selected)
        st.write(f"**Status:** {r['status']}  |  **Activity:** {r['activity']}  |  **Quantity:** {r['requested_qty']} {r['unit']}")
        st.json(json.loads(r['ai_review'] or '{}'))
        st.markdown('<div class="human"><b>Human approval gate</b><br>AI has prepared findings only. The consultant/client must decide whether the work is approved for execution.</div>', unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        if c1.button('✅ Approve Work', key='approve_cr', use_container_width=True):
            update_check_request(selected,status='APPROVED_FOR_EXECUTION',human_decision='APPROVED',actor=consultant)
            st.success('Work approved by human decision-maker.')
        if c2.button('↩️ Return for Correction', key='return_cr', use_container_width=True):
            update_check_request(selected,status='RETURNED_FOR_CORRECTION',human_decision='RETURNED',actor=consultant)
            st.warning('Returned for correction.')
        if c3.button('❌ Reject Work', key='reject_cr', use_container_width=True):
            update_check_request(selected,status='REJECTED',human_decision='REJECTED',actor=consultant)
            st.error('Work rejected by human decision-maker.')
    else: st.info('No Check Requests for this project yet.')

    st.divider(); st.header('IPC Generation')
    approved=[r for r in rows if r['status']=='APPROVED_FOR_EXECUTION']
    if approved:
        cr=st.selectbox('Approved Check Request for IPC', [r['request_no'] for r in approved], key='ipc_cr')
        r=get_check_request(cr)
        with st.form('ipc_form'):
            period_from=st.date_input('Period from', date.today().replace(day=1))
            period_to=st.date_input('Period to', date.today())
            current_qty=st.number_input('Executed quantity this period', min_value=0.0, value=float(r['requested_qty']), step=0.01)
            cumulative_qty=st.number_input('Cumulative executed quantity', min_value=0.0, value=float(r['requested_qty']), step=0.01)
            rate=st.number_input('BOQ rate', min_value=0.0, step=0.01)
            retention_pct=st.number_input('Retention %', min_value=0.0, max_value=100.0, value=10.0, step=0.5)
            ipc_docs=st.file_uploader('IPC supporting documents', type=['pdf','docx','xlsx','csv','jpg','jpeg','png'], accept_multiple_files=True, key='ipc_docs')
            make_ipc=st.form_submit_button('🧾 Generate IPC for Approved Work', type='primary', use_container_width=True)
        if make_ipc:
            current_amount=current_qty*rate; cumulative_amount=cumulative_qty*rate; retention=cumulative_amount*retention_pct/100; net_amount=current_amount-(current_amount*retention_pct/100)
            ipc_no=next_number('IPC','ipcs','ipc_no')
            data={'ipc_no':ipc_no,'project':project,'check_request_no':cr,'activity':r['activity'],'period_from':str(period_from),'period_to':str(period_to),'current_qty':current_qty,'cumulative_qty':cumulative_qty,'rate':rate,'current_amount':current_amount,'cumulative_amount':cumulative_amount,'retention':retention,'net_amount':net_amount,'documents':[d.name for d in ipc_docs] if ipc_docs else [],'document_paths':save_uploaded_files(ipc_docs, ipc_no),'actor':consultant}
            create_ipc(data)
            st.session_state.active_agent='IPC Preparation Agent'
            with st.status('AI workforce validating IPC…', expanded=True) as status:
                result=run_ipc_review(json.dumps(data, indent=2))
                status.update(label='IPC prepared — waiting for human approval', state='complete')
            update_ipc(ipc_no,ai_review={'crew_output':str(result)},actor='AI Workforce')
            st.success(f'IPC {ipc_no} generated for approved Check Request {cr}. Human approval is required.')
    else: st.info('No human-approved Check Requests are available for IPC generation.')

with client_tab:
    st.header('Client Workspace')
    st.caption('Final decision authority. The AI cannot approve works or payment.')
    pending=[r for r in list_check_requests(project) if r['status']=='AWAITING_HUMAN_APPROVAL']
    st.subheader('Pending Check Request Decisions')
    if pending:
        for r in pending:
            with st.container(border=True):
                st.write(f"**{r['request_no']}** · {r['activity']} · {r['requested_qty']} {r['unit']}")
                a,b=st.columns(2)
                if a.button('Approve execution', key=f"client_a_{r['request_no']}", type='primary'):
                    update_check_request(r['request_no'],status='APPROVED_FOR_EXECUTION',human_decision='APPROVED',actor=client); st.success('Approved for execution.'); st.rerun()
                if b.button('Reject / return', key=f"client_r_{r['request_no']}"):
                    update_check_request(r['request_no'],status='REJECTED',human_decision='REJECTED',actor=client); st.error('Rejected.'); st.rerun()
    else: st.info('No pending Check Requests.')

    st.subheader('Pending IPC Decisions')
    pending_ipcs=[i for i in list_ipcs(project) if not i['human_decision']]
    if pending_ipcs:
        for i in pending_ipcs:
            with st.container(border=True):
                st.write(f"**{i['ipc_no']}** · {i['activity']} · Current amount: {i['current_amount']:,.2f} · Net: {i['net_amount']:,.2f}")
                st.caption(f"Linked Check Request: {i['check_request_no']}")
                x,y=st.columns(2)
                if x.button('Approve IPC', key=f"ipc_a_{i['ipc_no']}", type='primary'):
                    update_ipc(i['ipc_no'],human_decision='APPROVED',actor=client); st.success('IPC approved by human.'); st.rerun()
                if y.button('Return IPC', key=f"ipc_r_{i['ipc_no']}"):
                    update_ipc(i['ipc_no'],human_decision='RETURNED_FOR_CORRECTION',actor=client); st.warning('IPC returned for correction.'); st.rerun()
    else: st.info('No pending IPCs.')
    st.markdown('<div class="danger"><b>Financial control:</b> This application generates and reviews IPCs; it does not execute bank transfers or autonomous payment releases.</div>', unsafe_allow_html=True)

with records_tab:
    st.header('Historical Records & Audit Trail')
    crs=list_check_requests(project); ipcs=list_ipcs(project)
    st.subheader('Check Request History')
    if crs:
        df=pd.DataFrame([{k:r[k] for k in ['request_no','activity','requested_qty','unit','status','human_decision','created_at','updated_at']} for r in crs])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else: st.info('No records.')
    st.subheader('IPC History')
    if ipcs:
        df=pd.DataFrame([{k:i[k] for k in ['ipc_no','check_request_no','activity','current_qty','rate','current_amount','net_amount','human_decision','created_at']} for i in ipcs])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else: st.info('No IPC records.')
