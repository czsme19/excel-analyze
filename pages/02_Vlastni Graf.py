import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Pokročilá Pivot Analýza",
    page_icon=":bar_chart:",  # zvol si jakýkoli emoji
    layout="wide"
)

def load_data():
    """
    Zkusíme načíst df z session_state nebo necháme uživatele nahrát soubor.
    """
    if "df" in st.session_state:
        return st.session_state["df"]
    else:
        uploaded_file = st.file_uploader("Nahraj Excel pro vlastní grafy", type=["xlsx"])
        if uploaded_file:
            df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=1)
            df = df_raw.rename(columns={
                df_raw.columns[1]: "Datum",
                df_raw.columns[2]: "Linie",
                df_raw.columns[3]: "PPlatz",
                df_raw.columns[4]: "Storort",
                df_raw.columns[5]: "Storort Popis",
                df_raw.columns[6]: "Fab Nr",
                df_raw.columns[7]: "Material Nr",
                df_raw.columns[8]: "Zarizeni",
                df_raw.columns[9]: "Material Nr 2",
                df_raw.columns[10]: "Material Popis",
                df_raw.columns[11]: "Fehler",
                df_raw.columns[12]: "Fehler Popis",
                df_raw.columns[13]: "Komentar"
            })
            df = df.dropna(subset=["Datum"])
            df["Datum"] = pd.to_datetime(df["Datum"])
            return df
        else:
            return None

def app():
    st.title(":bar_chart: Vlastní graf ")

    df = load_data()
    if df is None:
        st.info("Nahraj soubor nebo použij data z hlavní stránky (uložená v session_state).")
        return

    # 1) Filtry (stejné jako jinde)
    st.sidebar.header("Filtry (Vlastní graf)")
    with st.sidebar.expander("Rozbalit filtry"):
        datum_min = df["Datum"].min().date()
        datum_max = df["Datum"].max().date()
        datum_od = st.date_input("Od", datum_min)
        datum_do = st.date_input("Do", datum_max)

        linky = st.multiselect("Linky", df["Linie"].unique(), default=df["Linie"].unique())
        fehler_kod_filtr = st.multiselect("Fehler kód", df["Fehler"].dropna().unique(), default=df["Fehler"].dropna().unique())
        zarizeni_filtr = st.multiselect("Zařízení", df["Zarizeni"].dropna().unique(), default=df["Zarizeni"].dropna().unique())
        storort_popis_filtr = st.multiselect("Storort Bezeichnung", df["Storort Popis"].dropna().unique(), default=df["Storort Popis"].dropna().unique())
        fehler_popis_filtr = st.multiselect("Fehler Popis", df["Fehler Popis"].dropna().unique(), default=df["Fehler Popis"].dropna().unique())

    # Aplikace filtrů
    df_filtered = df[
        (df["Datum"].dt.date >= datum_od) &
        (df["Datum"].dt.date <= datum_do) &
        (df["Linie"].isin(linky)) &
        (df["Fehler"].isin(fehler_kod_filtr)) &
        (df["Zarizeni"].isin(zarizeni_filtr)) &
        (df["Storort Popis"].isin(storort_popis_filtr)) &
        (df["Fehler Popis"].isin(fehler_popis_filtr))
    ]

    st.subheader("Definuj si vlastní graf")

    # 2) Vyber si typ grafu
    chart_types = ["Bar", "Line", "Scatter", "Histogram", "Box"]
    selected_chart_type = st.selectbox("Typ grafu", chart_types)

    # 3) Vyber x a y
    all_cols = df_filtered.columns.tolist()
    x_axis = st.selectbox("X-axis", all_cols, index=1)
    y_axis = st.selectbox("Y-axis (pokud dává smysl)", [None] + all_cols, index=0)

    # Možnost vybrat "color"
    color_col = st.selectbox("Rozlišení podle (color)", [None] + all_cols, index=0)

    # 4) Vytvoříme graf podle vybraného typu (s většími rozměry)
    fig = None

    if selected_chart_type == "Bar":
        fig = px.bar(
            df_filtered,
            x=x_axis,
            y=y_axis,
            color=color_col if color_col else None,
            title=f"{selected_chart_type} graf",
            width=1200,
            height=700
        )
    elif selected_chart_type == "Line":
        fig = px.line(
            df_filtered,
            x=x_axis,
            y=y_axis,
            color=color_col if color_col else None,
            title=f"{selected_chart_type} graf",
            width=1200,
            height=700
        )
    elif selected_chart_type == "Scatter":
        fig = px.scatter(
            df_filtered,
            x=x_axis,
            y=y_axis,
            color=color_col if color_col else None,
            title=f"{selected_chart_type} graf",
            width=1200,
            height=700
        )
    elif selected_chart_type == "Histogram":
        fig = px.histogram(
            df_filtered,
            x=x_axis,
            color=color_col if color_col else None,
            title=f"{selected_chart_type} graf",
            width=1200,
            height=700
        )
    elif selected_chart_type == "Box":
        fig = px.box(
            df_filtered,
            x=x_axis,
            y=y_axis,
            color=color_col if color_col else None,
            title=f"{selected_chart_type} graf",
            width=1200,
            height=700
        )

    if fig is not None:
        # Pozn.: use_container_width=False, aby se bral v potaz width=1200
        st.plotly_chart(fig, use_container_width=False)
    else:
        st.info("Zvol typ grafu pro zobrazení.")

def run():
    app()

run()
