import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
from io import BytesIO
from fpdf import FPDF
import tempfile
import plotly.io as pio
import os

# Nastavení zobrazení: ikona a titul stránky
st.set_page_config(
    page_title="Dashboard - Výjezdy do oprav",
    page_icon=":sparkles:",
    layout="wide"
)

# V hlavním titulku rovněž zobrazíme ikonu
st.title(":sparkles: Dashboard - Výjezdy do oprav")

uploaded_file = st.file_uploader("Nahraj Excel report", type=["xlsx"])

if uploaded_file:
    # Načtení dat
    df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=1)

    # Přejmenování sloupců
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

    # Uložení df do session_state (pro další stránky)
    st.session_state["df"] = df

    # ------------- POSTRANNÍ FILTRY v expandru -------------
    st.sidebar.header("Filtry")
    with st.sidebar.expander("Rozbalit filtry"):
        datum_od = st.date_input("Od", df["Datum"].min().date())
        datum_do = st.date_input("Do", df["Datum"].max().date())

        linky = st.multiselect("Linky", df["Linie"].unique(), default=df["Linie"].unique())
        # zobrazení počtu vybraných linek
        st.metric("Počet vybraných linek", len(linky))

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

    # -------------------- PŘEHLED DAT --------------------
    
    st.subheader("Přehled dat")
    st.dataframe(df_filtered, use_container_width=True)

    # ----- DYNAMICKÁ KONTINGENČNÍ TABULKA (ZÁKLAD) -----
    st.subheader("Kontingenční analýza (pivot)")
    possible_cols = df_filtered.columns.tolist()
    index_col = st.selectbox("Index (řádky)", possible_cols, index=1)
    columns_col = st.selectbox("Columns (sloupce)", possible_cols, index=12)
    agg_method = st.selectbox("Typ agregace", ["count", "sum", "mean"], index=0)
    values_col = "Fehler"

    func = {"count": "count", "sum": "sum", "mean": "mean"}[agg_method]

    pivot_table_dynamic = pd.pivot_table(
        df_filtered,
        index=index_col,
        columns=columns_col,
        values=values_col,
        aggfunc=func,
        fill_value=0
    )
    st.dataframe(pivot_table_dynamic, use_container_width=True)

    # ------------------------- GRAFY -------------------------
    st.subheader("Počet chyb dle Fehler Bezeichung")
    fehler_counts = df_filtered["Fehler Popis"].value_counts().reset_index()
    fehler_counts.columns = ["Fehler Popis", "Pocet"]
    fig1 = px.bar(
        fehler_counts.head(10),
        x="Pocet",
        y="Fehler Popis",
        orientation="h",
        title="Top 10 Fehler Popis",
        height=400
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Počet chyb dle Fehler kódu a zařízení")
    fehler_kod_counts = df_filtered["Fehler"].value_counts().reset_index()
    fehler_kod_counts.columns = ["Fehler", "Pocet"]
    pie_data = df_filtered["Zarizeni"].value_counts().reset_index()
    pie_data.columns = ["Zarizeni", "Pocet"]

    col_kod, col_zar = st.columns(2)
    with col_kod:
        fig_kod = px.pie(
            fehler_kod_counts.head(10),
            names="Fehler",
            values="Pocet",
            title="Top 10 Fehler kód",
            height=500
        )
        fig_kod.update_traces(textinfo='value+percent', textposition='inside')
        st.plotly_chart(fig_kod, use_container_width=True)
    with col_zar:
        fig_zar = px.pie(
            pie_data.head(5),
            names="Zarizeni",
            values="Pocet",
            title="Top 5 Zařízení",
            height=500
        )
        fig_zar.update_traces(textinfo='value+percent', textposition='inside')
        st.plotly_chart(fig_zar, use_container_width=True)

    st.subheader("Paretův graf - Storort Bezeichnung")
    pareto_storort = df_filtered["Storort Popis"].value_counts().reset_index()
    pareto_storort.columns = ["Storort Popis", "Pocet"]
    pareto_storort["Kumulativní %"] = pareto_storort["Pocet"].cumsum() / pareto_storort["Pocet"].sum() * 100
    fig_pareto_storort = px.bar(
        pareto_storort,
        x="Storort Popis",
        y="Pocet",
        title="Pareto analýza dle Storort Bezeichnung"
    )
    fig_pareto_storort.add_scatter(
        x=pareto_storort["Storort Popis"],
        y=pareto_storort["Kumulativní %"],
        mode="lines+markers",
        name="Kumulativní %",
        yaxis="y2"
    )
    fig_pareto_storort.update_layout(
        yaxis=dict(title="Počet"),
        yaxis2=dict(title="Kumulativní %", overlaying="y", side="right", range=[0, 100]),
        legend=dict(x=0.8, y=1.15),
        height=500
    )
    st.plotly_chart(fig_pareto_storort, use_container_width=True)

    st.subheader("Počet chyb dle Storort Bezeichnung")
    storort_counts = df_filtered["Storort Popis"].value_counts().reset_index()
    storort_counts.columns = ["Storort Popis", "Pocet"]
    fig1b = px.bar(
        storort_counts.head(10),
        x="Pocet",
        y="Storort Popis",
        orientation="h",
        title="Top 10 Storort Bezeichnung",
        height=400
    )
    st.plotly_chart(fig1b, use_container_width=True)

    st.subheader("Počet chyb v čase")
    time_series = df_filtered.groupby(df_filtered["Datum"].dt.date).size().reset_index(name="Pocet")
    fig2 = px.line(time_series, x="Datum", y="Pocet", title="Počet chyb v čase")
    st.plotly_chart(fig2, use_container_width=True)

    # Nová sekce: agregovaný počet chyb podle Linie
    
    st.subheader("Počet chyb dle Linie")
    linie_counts = df_filtered["Linie"].value_counts().reset_index()
    linie_counts.columns = ["Linie", "Pocet"]
    fig_linie = px.bar(
        linie_counts,
        x="Linie",
        y="Pocet",
        title="Počet chyb dle Linie"
    )
    st.plotly_chart(fig_linie, use_container_width=True)

    st.subheader("Heatmapa četnosti chyb podle PPlatz a Linie")
    pivot_table = df_filtered.pivot_table(
        index="PPlatz",
        columns="Linie",
        values="Fehler",
        aggfunc="count",
        fill_value=0
    )
    st.dataframe(pivot_table.style.background_gradient(cmap="YlOrRd"))

    # ------------------------- DETAILNÍ ZÁZNAM VYBRANÉ CHYBY -------------------------
    st.subheader("Detailní záznamy chyb")
    selected_index = st.selectbox("Vyber řádek pro detail", df_filtered.index)
    if selected_index is not None:
        st.write(df_filtered.loc[selected_index])

    # ------------------------- DALŠÍ FILTROVÁNÍ -------------------------------------
    st.subheader("Chyby dle PPlatz, Linie a Fehler")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_pplatz = st.selectbox("Vyber PPlatz", df_filtered["PPlatz"].dropna().unique())
    with col2:
        selected_linie = st.selectbox("Vyber Linie", df_filtered["Linie"].dropna().unique())
    with col3:
        selected_fehler = st.selectbox("Vyber Fehler", df_filtered["Fehler"].dropna().unique())

    filtered_detail = df_filtered[
        (df_filtered["PPlatz"] == selected_pplatz) &
        (df_filtered["Linie"] == selected_linie) &
        (df_filtered["Fehler"] == selected_fehler)
    ][["Datum", "Storort Popis", "Komentar"]]

    st.dataframe(filtered_detail, use_container_width=True)

    st.subheader("Chyby dle Linie a Storort Popis")
    col_linie, col_storort = st.columns(2)
    with col_linie:
        selected_linie_storort = st.selectbox("Vyber Linie", df_filtered["Linie"].dropna().unique(), key="linie_storort")
    with col_storort:
        selected_stororts = st.multiselect("Vyber Storort Popis", df_filtered["Storort Popis"].dropna().unique())

    filtered_storort_detail = df_filtered[
        (df_filtered["Linie"] == selected_linie_storort) &
        (df_filtered["Storort Popis"].isin(selected_stororts))
    ][["Datum", "PPlatz", "Storort Popis", "Komentar", "Fab Nr", "Material Nr", "Zarizeni"]]

    st.dataframe(filtered_storort_detail, use_container_width=True)

    st.success("Analýza úspěšně provedena")

else:
    st.info("Nahraj Excel soubor pro zobrazení analýzy.")
