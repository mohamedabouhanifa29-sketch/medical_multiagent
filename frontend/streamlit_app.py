import streamlit as st
import requests

API = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="MedAgent — Système Clinique IA",
    page_icon="🏥",
    layout="wide"
)

# ── CSS Professionnel ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

.main { background: #0f1117; }

.header-container {
    background: linear-gradient(135deg, #1a1f2e 0%, #16213e 100%);
    border: 1px solid #2d3561;
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 32px;
    display: flex;
    align-items: center;
    gap: 20px;
}

.step-indicator {
    display: flex;
    gap: 8px;
    margin-bottom: 32px;
    align-items: center;
}

.step {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 24px;
    font-size: 13px;
    font-weight: 500;
}

.step-active {
    background: #2d3561;
    color: #7c8cf8;
    border: 1px solid #4a5299;
}

.step-done {
    background: #0d2d1a;
    color: #34d399;
    border: 1px solid #065f46;
}

.step-inactive {
    background: #1a1f2e;
    color: #4b5563;
    border: 1px solid #1f2937;
}

.card {
    background: #1a1f2e;
    border: 1px solid #2d3561;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
}

.card-success {
    background: #0d2d1a;
    border: 1px solid #065f46;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
}

.card-warning {
    background: #2d1f0d;
    border: 1px solid #92400e;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
}

.card-danger {
    background: #2d0d0d;
    border: 1px solid #7f1d1d;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 16px;
}

.metric-row {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
}

.metric-card {
    flex: 1;
    background: #1a1f2e;
    border: 1px solid #2d3561;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
}

.badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}

.badge-blue { background: #1e3a5f; color: #60a5fa; }
.badge-green { background: #0d2d1a; color: #34d399; }
.badge-red { background: #2d0d0d; color: #f87171; }

.divider {
    height: 1px;
    background: #2d3561;
    margin: 24px 0;
}

.report-section {
    background: #1a1f2e;
    border-left: 4px solid #7c8cf8;
    border-radius: 0 8px 8px 0;
    padding: 16px 20px;
    margin-bottom: 12px;
}

stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────
defaults = {
    "thread_id": None, "step": "start",
    "current_question": "", "question_count": 0,
    "diagnostic_summary": "", "interim_care": "",
    "final_report": "", "patient_case": ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Header ─────────────────────────────────────────────
st.markdown("""
<div class="header-container">
    <div style="font-size:48px">🏥</div>
    <div>
        <h1 style="margin:0; color:#e2e8f0; font-size:28px; font-weight:700">MedAgent</h1>
        <p style="margin:0; color:#7c8cf8; font-size:14px; font-weight:500">Système Multi-Agents d'Orientation Clinique Préliminaire</p>
    </div>
    <div style="margin-left:auto">
        <span class="badge badge-blue">⚡ LangGraph</span>&nbsp;
        <span class="badge badge-blue">🤖 Groq LLM</span>&nbsp;
        <span class="badge badge-blue">🔧 MCP Tools</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Step Indicator ─────────────────────────────────────
steps = [
    ("1", "Cas Patient", "start"),
    ("2", "Diagnostic", "questions"),
    ("3", "Médecin", "medecin"),
    ("4", "Rapport", "rapport")
]
cols = st.columns(len(steps))
for i, (num, label, step_id) in enumerate(steps):
    with cols[i]:
        if st.session_state.step == step_id:
            st.markdown(f'<div class="step step-active">🔵 {num}. {label}</div>', unsafe_allow_html=True)
        elif steps.index((num, label, step_id)) < [s[2] for s in steps].index(st.session_state.step):
            st.markdown(f'<div class="step step-done">✅ {num}. {label}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="step step-inactive">○ {num}. {label}</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── ÉCRAN 1 ────────────────────────────────────────────
if st.session_state.step == "start":
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### 📋 Description du cas patient")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        patient_case = st.text_area(
            "Décrivez les symptômes et informations du patient :",
            placeholder="Ex: Patient de 45 ans, douleurs thoraciques depuis ce matin, légère fièvre à 38.5°C, essoufflement au moindre effort...",
            height=150, label_visibility="collapsed"
        )
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            if st.button("🚀 Démarrer", use_container_width=True, type="primary"):
                if patient_case.strip():
                    with st.spinner("Initialisation de la consultation..."):
                        res = requests.post(f"{API}/consultation/start", json={"patient_case": patient_case})
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.thread_id = data["thread_id"]
                            st.session_state.question_count = data["question_count"]
                            st.session_state.current_question = data["current_question"]
                            st.session_state.patient_case = patient_case
                            st.session_state.step = "questions"
                            st.rerun()
                        else:
                            st.error(f"Erreur API : {res.text}")
                else:
                    st.warning("Veuillez décrire le cas du patient.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("### ℹ️ Comment ça marche")
        st.markdown("""
        <div class="card">
        <p style="color:#94a3b8; font-size:14px; line-height:1.8">
        <b style="color:#e2e8f0">1.</b> Décrivez le cas patient<br>
        <b style="color:#e2e8f0">2.</b> Le DiagnosticAgent pose 5 questions<br>
        <b style="color:#e2e8f0">3.</b> Synthèse clinique générée par IA<br>
        <b style="color:#e2e8f0">4.</b> Validation par le médecin traitant<br>
        <b style="color:#e2e8f0">5.</b> Rapport final structuré
        </p>
        <div class="divider"></div>
        <p style="color:#f87171; font-size:12px">
        ⚠️ Ce système ne remplace pas une consultation médicale.
        </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🧪 Cas de test rapide")
        cases = {
            "🫁 Cas 1 — Rhume / Grippe": "Patient de 35 ans, toux sèche depuis 3 jours, fièvre à 38°C, fatigue.",
            "🚨 Cas 2 — Urgence grave": "Patient de 55 ans, douleur thoracique intense, difficultés à respirer, sueurs froides.",
            "😌 Cas 3 — Rien de grave": "Patient de 25 ans, léger mal de tête, pas de fièvre, stress au travail."
        }
        
        for label, case_text in cases.items():
            if st.button(label, use_container_width=True):
                with st.spinner("Démarrage..."):
                    res = requests.post(f"{API}/consultation/start", json={"patient_case": case_text})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.thread_id = data["thread_id"]
                        st.session_state.question_count = data["question_count"]
                        st.session_state.current_question = data["current_question"]
                        st.session_state.patient_case = case_text
                        st.session_state.step = "questions"
                        st.rerun()
                    else:
                        st.error(f"Erreur API : {res.text}")

# ── ÉCRAN 2 ────────────────────────────────────────────
elif st.session_state.step == "questions":
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### ❓ Questions diagnostiques")
        progress = st.session_state.question_count / 5
        st.progress(progress, text=f"Question {st.session_state.question_count} / 5")

        raw = st.session_state.current_question
        question_text = raw.split(": ", 1)[-1].replace(" → EN_ATTENTE", "") if ": " in raw else raw

        st.markdown(f"""
        <div class="card">
            <p style="color:#7c8cf8; font-size:12px; font-weight:600; margin-bottom:8px">
                QUESTION {st.session_state.question_count} SUR 5
            </p>
            <p style="color:#e2e8f0; font-size:18px; font-weight:500; margin:0">
                {question_text}
            </p>
        </div>
        """, unsafe_allow_html=True)

        answer = st.text_input("Votre réponse :", placeholder="Répondez ici...", label_visibility="collapsed")
        if st.button("➡️ Soumettre la réponse", use_container_width=True, type="primary"):
            if answer.strip():
                with st.spinner("Analyse en cours..."):
                    res = requests.post(f"{API}/consultation/resume", json={
                        "thread_id": st.session_state.thread_id,
                        "patient_answer": answer
                    })
                    if res.status_code == 200:
                        data = res.json()
                        if data["status"] == "en_cours":
                            st.session_state.question_count = data["question_count"]
                            st.session_state.current_question = data["current_question"]
                            st.rerun()
                        elif data["status"] == "attente_medecin":
                            st.session_state.diagnostic_summary = data["diagnostic_summary"]
                            st.session_state.interim_care = data["interim_care"]
                            st.session_state.step = "medecin"
                            st.rerun()
            else:
                st.warning("Veuillez entrer une réponse.")

    with col2:
        st.markdown("### 📁 Cas en cours")
        st.markdown(f"""
        <div class="card">
            <p style="color:#7c8cf8; font-size:11px; font-weight:600">CAS PATIENT</p>
            <p style="color:#94a3b8; font-size:13px">{st.session_state.patient_case}</p>
            <div class="divider"></div>
            <p style="color:#7c8cf8; font-size:11px; font-weight:600">SESSION ID</p>
            <p style="color:#4b5563; font-size:11px; font-family:monospace">{st.session_state.thread_id[:16] if st.session_state.thread_id else "—"}...</p>
        </div>
        """, unsafe_allow_html=True)

# ── ÉCRAN 3 ────────────────────────────────────────────
elif st.session_state.step == "medecin":
    st.markdown("### 👨‍⚕️ Revue du médecin traitant")
    st.markdown("""
    <div class="card" style="border-color:#f59e0b">
        <p style="color:#f59e0b; font-size:13px; font-weight:600; margin:0">
        ⏸️ WORKFLOW EN PAUSE — Human-in-the-Loop actif
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🔬 Synthèse clinique préliminaire")
        st.markdown(f"""
        <div class="card-success">
            <p style="color:#d1fae5; font-size:14px; line-height:1.8">
                {st.session_state.diagnostic_summary}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 💊 Recommandation intermédiaire")
        st.markdown(f"""
        <div class="card-warning">
            <p style="color:#fde68a; font-size:14px; line-height:1.8">
                {st.session_state.interim_care}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("#### ✍️ Prescription du médecin traitant")
    treatment = st.text_area(
        "Traitement :",
        placeholder="Ex: Paracétamol 500mg toutes les 6h, repos 3 jours, réévaluation dans 48h si aggravation...",
        height=120, label_visibility="collapsed"
    )
    col_b1, col_b2 = st.columns([1, 3])
    with col_b1:
        if st.button("✅ Valider et générer", use_container_width=True, type="primary"):
            if treatment.strip():
                with st.spinner("Génération du rapport final..."):
                    res = requests.post(f"{API}/consultation/resume", json={
                        "thread_id": st.session_state.thread_id,
                        "physician_treatment": treatment
                    })
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.final_report = data["final_report"]
                        st.session_state.step = "rapport"
                        st.rerun()
            else:
                st.warning("Veuillez entrer un traitement.")

# ── ÉCRAN 4 ────────────────────────────────────────────
elif st.session_state.step == "rapport":
    st.markdown("### 📄 Rapport Clinique Final")
    st.markdown("""
    <div class="card-success">
        <p style="color:#34d399; font-size:14px; font-weight:600; margin:0">
        ✅ Consultation terminée avec succès
        </p>
    </div>
    """, unsafe_allow_html=True)

    lines = st.session_state.final_report.split('\n')
    current_section = ""
    content_lines = []

    section_icons = {
        "CAS": "👤", "RÉPONSES": "💬", "SYNTHÈSE": "🔬",
        "RECOMMANDATION": "💊", "TRAITEMENT": "👨‍⚕️",
        "INFORMATION": "🔧", "NIVEAU": "🚨"
    }

    for line in lines:
        line = line.strip()
        if not line:
            continue
        is_section = any(line.startswith(k) for k in section_icons.keys())
        if is_section or line.startswith("⚠️"):
            if current_section and content_lines:
                icon = section_icons.get(current_section.split()[0], "📌")
                content = "<br>".join(content_lines)
                color = "#f87171" if "URGENCE" in current_section else "#e2e8f0"
                st.markdown(f"""
                <div class="report-section">
                    <p style="color:#7c8cf8; font-size:11px; font-weight:700; margin-bottom:8px">
                        {icon} {current_section}
                    </p>
                    <p style="color:{color}; font-size:14px; line-height:1.8; margin:0">
                        {content}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                content_lines = []
            if line.startswith("⚠️"):
                st.markdown(f"""
                <div class="card-danger">
                    <p style="color:#f87171; font-size:13px; font-weight:600; margin:0">{line}</p>
                </div>
                """, unsafe_allow_html=True)
                current_section = ""
            else:
                current_section = line.replace(":", "").strip()
        else:
            content_lines.append(line)

    if current_section and content_lines:
        icon = section_icons.get(current_section.split()[0], "📌")
        content = "<br>".join(content_lines)
        st.markdown(f"""
        <div class="report-section">
            <p style="color:#7c8cf8; font-size:11px; font-weight:700; margin-bottom:8px">
                {icon} {current_section}
            </p>
            <p style="color:#e2e8f0; font-size:14px; line-height:1.8; margin:0">
                {content}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    if st.button("🔄 Nouvelle consultation", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()