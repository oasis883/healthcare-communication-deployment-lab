import os
from datetime import datetime


import streamlit as st
from dotenv import load_dotenv

load_dotenv()

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

st.set_page_config(page_title='Healthcare Communication Deployment Lab', page_icon='🏥', layout='wide')


def init_state() -> None:
    defaults: dict[str, Any] = {
        'patient': None,
        'hl7_message': '',
        'alert': None,
        'wifi_dbm': -60,
        'delivery_status': 'Not tested',
        'logs': [],
        'ai_review': '',
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_log(message: str) -> None:
    st.session_state.logs.insert(0, f"{datetime.now().strftime('%H:%M:%S')} — {message}")


def clean(value: str) -> str:
    return value.replace('|', ' ').replace('^', ' ').strip()


def generate_hl7(patient: dict[str, str]) -> str:
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    parts = patient['name'].split()
    family = clean(parts[-1]) if parts else 'UNKNOWN'
    given = clean(' '.join(parts[:-1])) if len(parts) > 1 else 'UNKNOWN'
    return '\n'.join([
        f"MSH|^~\\&|EHR|DEMO_HOSPITAL|COMM_SYSTEM|DEMO_HOSPITAL|{timestamp}||ADT^A01|MSG00001|P|2.5",
        f"PID|1||{clean(patient['patient_id'])}||{family}^{given}||{patient['dob'].replace('-', '')}|{patient['gender'][:1].upper()}",
        f"PV1|1|I|{clean(patient['ward'])}^{clean(patient['room'])}^{clean(patient['bed'])}",
    ])


def assess_wifi(dbm: int) -> tuple[str, str, str]:
    if dbm >= -55:
        return 'Excellent', 'Expected to support reliable voice and alert delivery.', 'success'
    if dbm >= -67:
        return 'Good', 'Generally suitable for voice and alert delivery.', 'success'
    if dbm >= -75:
        return 'Weak', 'Voice or alert delivery may become unreliable.', 'warning'
    return 'Poor', 'High risk of delayed or failed delivery.', 'error'


def delivery_result(dbm: int) -> str:
    if dbm >= -67:
        return 'Delivered successfully'
    if dbm >= -75:
        return 'Delivered with potential delay'
    return 'Delivery failed in simulation'


def review_context() -> str:
    patient = st.session_state.patient or {}
    alert = st.session_state.alert or {}
    status, _, _ = assess_wifi(st.session_state.wifi_dbm)
    return f"""
SIMULATED DEPLOYMENT RESULTS

Patient:
- ID: {patient.get('patient_id', 'Not created')}
- Ward: {patient.get('ward', 'Not assigned')}
- Room: {patient.get('room', 'Not assigned')}
- Bed: {patient.get('bed', 'Not assigned')}

HL7:
- Message generated: {'Yes' if st.session_state.hl7_message else 'No'}

Nurse call:
- Alert type: {alert.get('type', 'Not triggered')}
- Priority: {alert.get('priority', 'Not available')}
- Delivery: {st.session_state.delivery_status}

Wireless:
- Signal: {st.session_state.wifi_dbm} dBm
- Status: {status}

Review this as a senior healthcare IT implementation engineer. Provide:
1. Successful checks
2. Risks or failed checks
3. Likely technical causes
4. Recommended troubleshooting actions
5. Go-live recommendation: READY, READY WITH CONDITIONS, or NOT READY

Do not provide medical advice.
""".strip()


def analyse_with_claude(context: str) -> str:
    if Anthropic is None:
        raise RuntimeError('The anthropic package is not installed.')
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        try:
            api_key = st.secrets['ANTHROPIC_API_KEY']
        except Exception:
            api_key = None
    if not api_key:
        raise RuntimeError('ANTHROPIC_API_KEY was not found.')
    model = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=900,
        temperature=0.2,
        system='You are a senior healthcare IT implementation engineer. Analyse only technical deployment, integration, networking, testing and go-live concerns. Do not provide medical advice.',
        messages=[{'role': 'user', 'content': context}],
    )
    return '\n'.join(block.text for block in response.content if getattr(block, 'type', None) == 'text').strip()


init_state()

st.title('🏥 Healthcare Communication Deployment Lab')
st.caption('Synthetic learning simulator for HL7, nurse-call alerts, wireless assessment, go-live testing and Claude-assisted review.')

with st.sidebar:
    st.header('Deployment status')
    st.write(f"Patient configured: {'✅' if st.session_state.patient else '⬜'}")
    st.write(f"HL7 generated: {'✅' if st.session_state.hl7_message else '⬜'}")
    st.write(f"Nurse call tested: {'✅' if st.session_state.alert else '⬜'}")
    st.write(f"Wireless assessed: {'✅' if st.session_state.delivery_status != 'Not tested' else '⬜'}")
    if st.button('Reset simulation', use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs(['1. Patient & HL7', '2. Nurse Call', '3. Wireless', '4. Go-Live Review', '5. Event Log'])

with tab1:
    st.subheader('Patient admission and HL7 ADT simulation')
    st.info('Use fictional information only.')
    with st.form('patient_form'):
        c1, c2 = st.columns(2)
        with c1:
            patient_name = st.text_input('Patient name', 'Maya Sharma')
            patient_id = st.text_input('Patient ID', 'P1001')
            dob = st.date_input('Date of birth', datetime(1995, 5, 18))
        with c2:
            gender = st.selectbox('Gender', ['Female', 'Male', 'Other', 'Unknown'])
            ward = st.text_input('Ward', 'Cardiology')
            room = st.text_input('Room', '210')
            bed = st.text_input('Bed', '2')
        submitted = st.form_submit_button('Admit patient and generate HL7', type='primary')

    if submitted:
        if not all([patient_name.strip(), patient_id.strip(), ward.strip(), room.strip(), bed.strip()]):
            st.error('Complete all required fields.')
        else:
            patient = {
                'name': patient_name.strip(),
                'patient_id': patient_id.strip(),
                'dob': dob.isoformat(),
                'gender': gender,
                'ward': ward.strip(),
                'room': room.strip(),
                'bed': bed.strip(),
            }
            st.session_state.patient = patient
            st.session_state.hl7_message = generate_hl7(patient)
            st.session_state.alert = None
            st.session_state.delivery_status = 'Not tested'
            st.session_state.ai_review = ''
            add_log(f"Patient {patient['patient_id']} admitted to {patient['ward']} / Room {patient['room']} / Bed {patient['bed']}.")
            add_log('HL7 ADT^A01 message generated.')

    if st.session_state.patient:
        patient = st.session_state.patient
        st.success(f"{patient['name']} assigned to {patient['ward']}, Room {patient['room']}, Bed {patient['bed']}.")
        st.code(st.session_state.hl7_message, language='text')
        st.markdown('- `MSH`: message header\n- `PID`: patient details\n- `PV1`: ward, room and bed')

with tab2:
    st.subheader('Nurse-call workflow')
    if not st.session_state.patient:
        st.warning('Admit a patient first.')
    else:
        patient = st.session_state.patient
        st.write(f"Testing alerts for **{patient['name']} — {patient['ward']}, Room {patient['room']}, Bed {patient['bed']}**")
        c1, c2, c3 = st.columns(3)
        choice = None
        with c1:
            if st.button('Normal assistance', use_container_width=True):
                choice = ('Normal Assistance', 'Normal')
        with c2:
            if st.button('Urgent assistance', use_container_width=True):
                choice = ('Urgent Assistance', 'High')
        with c3:
            if st.button('Emergency', type='primary', use_container_width=True):
                choice = ('Emergency Call', 'Critical')
        if choice:
            st.session_state.alert = {
                'type': choice[0],
                'priority': choice[1],
                'patient': patient['name'],
                'location': f"{patient['ward']} / Room {patient['room']} / Bed {patient['bed']}",
                'device': 'Nurse Device 01',
            }
            st.session_state.delivery_status = delivery_result(st.session_state.wifi_dbm)
            add_log(f"{choice[0]} triggered with {choice[1]} priority.")
            add_log(f"Alert result: {st.session_state.delivery_status} at {st.session_state.wifi_dbm} dBm.")
        if st.session_state.alert:
            alert = st.session_state.alert
            st.error(f"🚨 {alert['type']} — {alert['priority']} priority")
            a, b, c = st.columns(3)
            a.metric('Patient', alert['patient'])
            b.metric('Location', alert['location'])
            c.metric('Assigned device', alert['device'])
            st.code('Bedside Call Button\n        ↓\nNurse Call System\n        ↓\nClinical Communication Server\n        ↓\nHospital Network and Wi-Fi\n        ↓\nAssigned Nurse Device', language='text')
            st.write(f"**Delivery result:** {st.session_state.delivery_status}")

with tab3:
    st.subheader('Simulated voice-grade Wi-Fi assessment')
    value = st.slider('Signal strength (dBm)', -90, -35, int(st.session_state.wifi_dbm))
    if value != st.session_state.wifi_dbm:
        st.session_state.wifi_dbm = value
        if st.session_state.alert:
            st.session_state.delivery_status = delivery_result(value)
        status, _, _ = assess_wifi(value)
        add_log(f"Wireless assessment updated to {value} dBm ({status}).")
    status, explanation, level = assess_wifi(st.session_state.wifi_dbm)
    a, b = st.columns(2)
    a.metric('Signal strength', f"{st.session_state.wifi_dbm} dBm")
    b.metric('Assessment', status)
    if level == 'success':
        st.success(explanation)
    elif level == 'warning':
        st.warning(explanation)
    else:
        st.error(explanation)
    if st.session_state.alert:
        st.write(f"**Simulated alert result:** {st.session_state.delivery_status}")

with tab4:
    st.subheader('Go-live validation and Claude review')
    checks = {
        'Patient and location configured': bool(st.session_state.patient),
        'HL7 ADT message generated': bool(st.session_state.hl7_message),
        'Nurse-call alert triggered': bool(st.session_state.alert),
        'Wireless signal is at least good': st.session_state.wifi_dbm >= -67,
        'Alert delivered successfully': st.session_state.delivery_status == 'Delivered successfully',
    }
    for label, passed in checks.items():
        st.write(f"{'✅' if passed else '❌'} {label}")
    passed = sum(checks.values())
    if passed == len(checks):
        st.success('Simulation status: READY FOR GO-LIVE')
    elif passed >= 3:
        st.warning('Simulation status: READY WITH CONDITIONS')
    else:
        st.error('Simulation status: NOT READY')

    if st.button('Analyse deployment with Claude', type='primary'):
        try:
            with st.spinner('Claude is reviewing the simulation...'):
                st.session_state.ai_review = analyse_with_claude(review_context())
            add_log('Claude implementation review generated.')
        except Exception as exc:
            st.error(str(exc))
    if st.session_state.ai_review:
        st.markdown(st.session_state.ai_review)
    else:
        with st.expander('Preview the information sent to Claude'):
            st.code(review_context(), language='text')

with tab5:
    st.subheader('Implementation event log')
    if not st.session_state.logs:
        st.info('No events recorded yet.')
    else:
        for item in st.session_state.logs:
            st.write(item)
    st.caption('Learning simulation only. Not connected to a real EHR, nurse-call system, Vocera environment or hospital wireless network.')
