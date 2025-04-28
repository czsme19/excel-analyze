import streamlit as st
import pandas as pd
import datetime

# Nastavíme zobrazení stránky včetně ikony 📊
st.set_page_config(
    page_title="Pokročilá kontingenční analýza",
    page_icon=":chart:",
    layout="wide"
)

def load_data():
    """
    Zkusí načíst `df` z session_state, nebo nechá uživatele nahrát nový soubor.
    """
    if "df" in st.session_state:
        return st.session_state["df"]
    uploaded_file = st.file_uploader(
        "Nahraj Excel (pro pokročilou pivot analýzu)", type=["xlsx"]
    )
    if not uploaded_file:
        return None
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


def app():
    st.title(":chart: Pokročilá kontingenční analýza")

    # 1) Načtení dat
    df = load_data()
    if df is None:
        st.info("Nahraj soubor pro pokročilou pivot analýzu nebo se vrať na hlavní stránku.")
        return

    # 2) Filtry
    st.sidebar.header("Filtry (Pivot stránka)")
    with st.sidebar.expander("Rozbalit filtry"):
        datum_min = df["Datum"].min().date()
        datum_max = df["Datum"].max().date()
        datum_od = st.date_input("Od", datum_min)
        datum_do = st.date_input("Do", datum_max)

        linky = st.multiselect("Linky", df["Linie"].unique(), default=df["Linie"].unique())
        fehler_kod_filtr = st.multiselect(
            "Fehler kód", df["Fehler"].dropna().unique(), default=df["Fehler"].dropna().unique()
        )
        zarizeni_filtr = st.multiselect(
            "Zařízení", df["Zarizeni"].dropna().unique(), default=df["Zarizeni"].dropna().unique()
        )
        storort_popis_filtr = st.multiselect(
            "Storort Bezeichnung", df["Storort Popis"].dropna().unique(), default=df["Storort Popis"].dropna().unique()
        )
        fehler_popis_filtr = st.multiselect(
            "Fehler Popis", df["Fehler Popis"].dropna().unique(), default=df["Fehler Popis"].dropna().unique()
        )

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

    st.markdown("""
    ### Pokročilá pivotka
    Zde si můžeš vybrat více sloupců pro **index** a **columns** a rovněž více sloupců pro `values` + definovat různé metody agregace.
    """
    )

    # 3) Výběr sloupců a agregací
    possible_cols = df_filtered.columns.tolist()
    index_cols = st.multiselect("Index (můžeš víc)", possible_cols, default=["Linie"])
    columns_cols = st.multiselect("Columns (můžeš víc)", possible_cols, default=["Fehler Popis"])
    values_cols = st.multiselect(
        "Values (můžeš víc)", ["Fehler","Fab Nr","Material Nr"], default=["Fehler"]
    )

    st.markdown("**Vyber metody agregace (můžeš zvolit více)**")
    agg_choices = {"count": "count", "sum": "sum", "mean": "mean"}
    selected_aggs = st.multiselect("Agregace", list(agg_choices.keys()), default=["count","sum"])

    agg_dict = {val_col: [agg_choices[a] for a in selected_aggs] for val_col in values_cols}
    add_margins = st.checkbox("Zobrazit součty (margins)", value=True)

    # 4) Vytvoření pivot tabulky bez vestavěných margins
    pivot_table_adv = pd.pivot_table(
        df_filtered,
        index=index_cols,
        columns=columns_cols,
        values=values_cols,
        aggfunc=agg_dict,
        fill_value=0,
        margins=False
    )

    # 5) Ruční přidání řádkových součtů, pokud je zaškrtnuto
    if add_margins:
        row_totals = pivot_table_adv.sum(axis=1)
        if isinstance(pivot_table_adv.index, pd.MultiIndex):
            total_row_name = tuple(["Celkem"] * pivot_table_adv.index.nlevels)
        else:
            total_row_name = "Celkem"
        pivot_table_adv.loc[total_row_name] = row_totals

    # Zobrazení výsledku
    st.dataframe(pivot_table_adv, use_container_width=True)


def run():
    app()

run()
