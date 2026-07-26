from datetime import date
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# --- CONFIGURAZIONE ---
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwqhJD87jDqC1Xtw79bJt19e4sznkyfu50xJJkQlNlLVzeqg8sSp9wuvL0GQFTmIqfU/exec"

st.set_page_config(
    page_title="Body Tracker", page_icon="📊", layout="centered"
)

# --- STILE CSS PERSONALIZZATO PER I BLOCCHETTI KPI ---
st.markdown(
    """
    <style>
    .kpi-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0.5,0,0.05);
        margin-bottom: 10px;
    }
    .kpi-title {
        font-size: 14px;
        color: #555555;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 20px;
        color: #0e1117;
        font-weight: bold;
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
            return pd.DataFrame(
                columns=[
                    "data",
                    "peso",
                    "massa grassa",
                    "massa magra",
                    "bmi",
                    "metabolismo basale",
                ]
            )
    except Exception as e:
        st.error(f"Errore di connessione al foglio: {e}")
        return pd.DataFrame(
            columns=[
                "data",
                "peso",
                "massa grassa",
                "massa magra",
                "bmi",
                "metabolismo basale",
            ]
        )


df = load_data()

st.title("🫀 Body Composition Tracker")

tab_dash, tab_add, tab_manage = st.tabs(
    ["📈 Dashboard", "➕ Inserisci", "⚙️ Gestisci / Modifica"]
)

# ================= TAB 1: DASHBOARD =================
with tab_dash:
    st.subheader("Panoramica e KPI")

    if not df.empty and "peso" in df.columns and len(df) > 0:
        df_sorted_desc = df.sort_values("data", ascending=False)
        latest = df_sorted_desc.iloc[0]

        bmr_val = latest.get("metabolismo basale", 0)
        tdee_val = int(bmr_val * 1.45) if bmr_val else 0

        # Creazione dei blocchetti KPI personalizzati in HTML/CSS
        kpis = [
            ("Peso", f"{latest['peso']} kg"),
            ("Massa Grassa", f"{latest.get('massa grassa', 0)}%"),
            ("BMI", f"{latest.get('bmi', 0)}"),
            ("BMR", f"{bmr_val} kcal"),
            ("TDEE stimato", f"{tdee_val} kcal"),
        ]

        # Dividiamo i 5 KPI in colonne
        cols = st.columns(5)
        for i, (title, val) in enumerate(kpis):
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">{title}</div>
                        <div class="kpi-value">{val}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()
        st.subheader("Tutti i Trend Storici")

        df_sorted = df.sort_values("data")

        metric_labels = {
            "peso": "Peso (kg)",
            "massa grassa": "Massa Grassa (%)",
            "massa magra": "Massa Magra (%)",
            "bmi": "BMI",
            "metabolismo basale": "Metabolismo Basale (kcal)",
        }

        for col_name, label in metric_labels.items():
            if col_name in df.columns:
                fig = px.line(
                    df_sorted,
                    x="data",
                    y=col_name,
                    markers=True,
                    title=f"Andamento: {label}",
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nessun dato presente nel foglio.")

# ================= TAB 2: INSERISCI DATI =================
with tab_add:
    st.subheader("Nuova Misurazione")

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

        submit = st.form_submit_button("Salva nel Database")

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
                st.success("Dati salvati con successo su Google Sheets! 🎉")
                st.rerun()
            else:
                st.error("Errore durante il salvataggio.")

# ================= TAB 3: GESTISCI / MODIFICA / CANCELLA =================
with tab_manage:
    st.subheader("Storico e Gestione Record")

    if not df.empty:
        edited_df = st.data_editor(df, num_rows="dynamic", key="editor_dati")

        if st.button("Aggiorna Google Sheet con le modifiche"):
            all_rows = [list(edited_df.columns)]
            for _, row in edited_df.iterrows():
                row_list = list(row)
                row_list[0] = str(row_list[0])
                all_rows.append(row_list)

            payload = {"action": "update", "data": all_rows}
            res = requests.post(WEB_APP_URL, json=payload)
            if res.status_code == 200:
                st.success("Google Sheet aggiornato correttamente!")
                st.rerun()
            else:
                st.error("Errore durante l'aggiornamento.")
    else:
        st.info("Nessun dato da gestire.")