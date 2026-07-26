from datetime import date
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# --- CONFIGURAZIONE ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwqhJD87jDqC1Xtw79bJt19e4sznkyfu50xJJkQlNlLVzeqg8sSp9wuvL0GQFTmIqfU/exec"

st.set_page_config(
    page_title="Body Tracker", page_icon="🫀", layout="centered"
)

# --- STILE CSS CUSTOM (UI/UX PREMIUM) ---
st.markdown(
    """
    <style>
    .main {
        background-color: #fafbfc;
    }
    
    /* Header stile App */
    .app-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 20px 0;
        border-bottom: 1px solid #eaecef;
        margin-bottom: 20px;
    }
    .app-title {
        font-size: 24px;
        font-weight: 800;
        color: #1f2328;
    }
    
    /* Card KPI Moderna */
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f4f6f9 100%);
        border: 1px solid #e1e4e8;
        border-radius: 14px;
        padding: 14px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        margin-bottom: 12px;
    }
    .kpi-title {
        font-size: 12px;
        color: #656d76;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 20px;
        color: #1f2328;
        font-weight: 800;
    }
    .kpi-delta {
        font-size: 11px;
        font-weight: 600;
        margin-top: 4px;
        color: #656d76;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- FUNZIONI PER LEGGERE E SCRIVERE SU GOOGLE SHEETS VIA WEB APP ---
def load_data():
    try:
        response = requests.post(WEB_APP_URL, json={"action": "read"})
        rows = response.json()
        if len(rows) > 1:
            headers = rows[0]
            data = rows[1:]
            df = pd.DataFrame(data, columns=headers)

            df.columns = df.columns.str.strip().str.lower()
            df["data"] = pd.to_datetime(df["data"]).dt.date

            for col in df.columns:
                if col != "data":
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Errore di connessione al foglio: {e}")
        return pd.DataFrame()


df = load_data()

# --- HEADER PERSONALIZZATO ---
st.markdown(
    """
    <div class="app-header">
        <div class="app-title">🫀 Body Tracker</div>
    </div>
""",
    unsafe_allow_html=True,
)

# ================= SEZIONE RAPIDA: AGGIUNGI (ESPANDIBILE TRAMITE "+") =================
with st.expander("➕ Aggiungi Nuova Misurazione", expanded=False):
    with st.form("form_inserimento", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            data_misura = st.date_input("Data", value=date.today())
            peso = st.number_input(
                "Peso (kg)", min_value=30.0, max_value=200.0, value=75.0, step=0.1
            )
            massa_grassa = st.number_input(
                "Massa Grassa (%)",
                min_value=1.0,
                max_value=60.0,
                value=20.0,
                step=0.1,
            )
        with col_b:
            massa_magra = st.number_input(
                "Massa Magra (%)",
                min_value=10.0,
                max_value=90.0,
                value=75.0,
                step=0.1,
            )
            bmi = st.number_input(
                "BMI", min_value=10.0, max_value=50.0, value=22.0, step=0.1
            )
            bmr = st.number_input(
                "Metabolismo Basale (kcal)",
                min_value=1000,
                max_value=3000,
                value=1700,
                step=10,
            )

        submit = st.form_submit_button(
            "Salva nel Database 🚀", use_container_width=True
        )

        if submit:
            payload = {
                "action": "append",
                "data": {
                    "date": str(data_misura),
                    "peso": peso,
                    "massa_grassa": massa_grassa,
                    "massa_magra": massa_magra,
                    "bmi": bmi,
                    "bmr": bmr,
                },
            }
            res = requests.post(WEB_APP_URL, json=payload)
            if res.status_code == 200:
                st.success("Registrato con successo! 🎉")
                st.rerun()
            else:
                st.error("Errore durante il salvataggio.")

# --- NAVIGAZIONE A MENU PULITA (TABS) ---
tab_dash, tab_manage = st.tabs(["📊 Dashboard & Trend", "⚙️ Gestisci Storico"])

# ================= TAB 1: DASHBOARD & TREND =================
with tab_dash:
    if not df.empty and "peso" in df.columns and len(df) > 0:
        df_sorted = df.sort_values("data")
        df_sorted_desc = df.sort_values("data", ascending=False)

        latest = df_sorted_desc.iloc[0]
        previous = df_sorted_desc.iloc[1] if len(df_sorted_desc) > 1 else None

        bmr_val = latest.get("metabolismo basale", 0)
        tdee_val = int(bmr_val * 1.45) if bmr_val else 0


        def get_delta(col_name):
            if (
                previous is not None
                and col_name in latest
                and col_name in previous
            ):
                diff = latest[col_name] - previous[col_name]
                sign = "+" if diff > 0 else ""
                return f"{sign}{diff:.1f}"
            return ""


        peso_delta = get_delta("peso")
        mg_delta = get_delta("massa grassa")

        st.markdown(
            "<p style='font-size: 15px; font-weight: 700; color: #1f2328; margin-bottom: 10px;'>Panoramica Recente</p>",
            unsafe_allow_html=True,
        )

        kpis = [
            ("Peso", f"{latest['peso']} kg", f"{peso_delta} kg vs prec."),
            (
                "Massa Grassa",
                f"{latest.get('massa grassa', 0)}%",
                f"{mg_delta}% vs prec.",
            ),
            ("BMI", f"{latest.get('bmi', 0)}", ""),
            ("BMR", f"{bmr_val} kcal", ""),
            ("TDEE Stimato", f"{tdee_val} kcal", "Attività 1.45"),
        ]

        cols = st.columns(3)
        for i, (title, val, delta) in enumerate(kpis):
            col_idx = i % 3
            with cols[col_idx]:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">{title}</div>
                        <div class="kpi-value">{val}</div>
                        <div class="kpi-delta">{delta}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<p style='font-size: 15px; font-weight: 700; color: #1f2328; margin: 20px 0 10px 0;'>Analisi Trend</p>",
            unsafe_allow_html=True,
        )

        metric_labels = {
            "peso": "Peso (kg)",
            "massa grassa": "Massa Grassa (%)",
            "massa magra": "Massa Magra (%)",
            "bmi": "BMI",
            "metabolismo basale": "Metabolismo Basale (kcal)",
        }

        for col_name, label in metric_labels.items():
            if col_name in df.columns:
                fig = go.Figure()
                fig.add_trace(
                    go.Scatter(
                        x=df_sorted["data"],
                        y=df_sorted[col_name],
                        mode="lines+markers",
                        name=label,
                        line=dict(color="#0969da", width=3),
                        marker=dict(size=7, color="#0969da"),
                        fill="tozeroy",
                        fillcolor="rgba(9, 105, 218, 0.05)",
                    )
                )

                fig.update_layout(
                    title=dict(text=label, font=dict(size=14, color="#1f2328")),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=10, t=35, b=10),
                    height=220,
                    xaxis=dict(showgrid=True, gridcolor="#f0f2f5"),
                    yaxis=dict(showgrid=True, gridcolor="#f0f2f5"),
                )

                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            "Nessun dato presente nel foglio. Espandi il menu in alto per inserire la prima misurazione!"
        )

# ================= TAB 2: GESTISCI STORICO =================
with tab_manage:
    st.markdown(
        "<p style='font-size: 15px; font-weight: 700; color: #1f2328; margin-bottom: 10px;'>Modifica o Elimina Registrazioni</p>",
        unsafe_allow_html=True,
    )

    if not df.empty:
        edited_df = st.data_editor(
            df, num_rows="dynamic", key="editor_dati", use_container_width=True
        )

        if st.button(
            "Salva Modifiche sul Foglio", use_container_width=True
        ):
            all_rows = [list(edited_df.columns)]
            for _, row in edited_df.iterrows():
                row_list = list(row)
                row_list[0] = str(row_list[0])
                all_rows.append(row_list)

            payload = {"action": "update", "data": all_rows}
            res = requests.post(WEB_APP_URL, json=payload)
            if res.status_code == 200:
                st.success("Google Sheet aggiornato con successo!")
                st.rerun()
            else:
                st.error("Errore durante l'aggiornamento.")
    else:
        st.info("Nessun dato da gestire.")