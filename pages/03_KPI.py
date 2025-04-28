import streamlit as st
import pandas as pd
import datetime
import plotly.express as px  # import for plotting

# Nastavení zobrazení stránky
st.set_page_config(
    page_title="Klíčové ukazatele (KPI)",
    page_icon=":bar_chart:",
    layout="wide"
)

def load_data():
    if "df" in st.session_state:
        return st.session_state["df"]
    st.info("Nejprve nahrajte data na hlavní stránce.")
    return None

# Načtení dat
df = load_data()
if df is None:
    st.stop()

st.title(":bar_chart: Klíčové ukazatele (KPI)")

# Filtry období
datum_min = df["Datum"].min().date()
datum_max = df["Datum"].max().date()
col1, col2 = st.columns(2)
with col1:
    datum_od = st.date_input("Období od", datum_min)
    datum_do = st.date_input("Období do", datum_max)
with col2:
    st.markdown("_Vyberte období, pro které chcete zobrazit KPI._")

# Kontrola rozsahu
days = (datum_do - datum_od).days + 1
n_days_text = f"({days} dní)" if days > 1 else "(1 den)"

# Filtrování dat
mask_cur = (df["Datum"].dt.date >= datum_od) & (df["Datum"].dt.date <= datum_do)
df_cur = df[mask_cur]

# Výpočty základních KPI
total_incidents = len(df_cur)
avg_per_day = total_incidents / days if days > 0 else 0

# Incidents per line a top line
line_counts = df_cur["Linie"].value_counts()
top_line = line_counts.idxmax() if not line_counts.empty else None
top_line_count = line_counts.max() if not line_counts.empty else 0
avg_per_line = line_counts.mean() if not line_counts.empty else 0

# Srovnání s předchozím obdobím
prev_end = datum_od - datetime.timedelta(days=1)
prev_start = prev_end - datetime.timedelta(days=days-1)
mask_prev = (df["Datum"].dt.date >= prev_start) & (df["Datum"].dt.date <= prev_end)
df_prev = df[mask_prev]
prev_total = len(df_prev)
delta_total = total_incidents - prev_total

delta_str = f"{delta_total:+d}"
if prev_total > 0:
    delta_pct = (delta_total / prev_total) * 100
    delta_str_pct = f" ({delta_pct:+.1f}% )"
else:
    delta_str_pct = ""

# Zobrazení základních KPI
st.markdown(f"### Období: {datum_od} až {datum_do} {n_days_text}")
col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Celkový počet výjezdů", total_incidents, delta_str + delta_str_pct)
col_b.metric("Průměr na den", f"{avg_per_day:.1f}")
col_c.metric("Nejkritičtější linka", top_line or "-", f"{top_line_count}")
col_d.metric("Průměr na linku", f"{avg_per_line:.1f}")

# Graf trendu v čase
st.subheader("Trend výjezdů v čase")
df_cur_ts = df_cur.groupby(df_cur["Datum"].dt.date).size().reset_index(name="Pocet")
fig_trend = px.line(df_cur_ts, x="Datum", y="Pocet", title="Počet výjezdů po dnech")
st.plotly_chart(fig_trend, use_container_width=True)

# Top 5 linek podle počtu výjezdů
st.subheader("Top 5 linek podle počtu výjezdů")
top5 = line_counts.head(5).reset_index()
top5.columns = ["Linie", "Pocet"]
fig_top5 = px.bar(top5, x="Linie", y="Pocet", title="Top 5 linek")
st.plotly_chart(fig_top5, use_container_width=True)

# Přehled podle Fehler kódu - výsečový graf
st.subheader("Chyby podle kódu (Fehler)")
code_counts = df_cur["Fehler"].value_counts().reset_index()
code_counts.columns = ["Fehler kód", "Pocet"]
fig_codes = px.pie(
    code_counts,
    names="Fehler kód",
    values="Pocet",
    title="Distribuce chyb podle kódu Fehler",
    height=400
)
fig_codes.update_traces(textinfo='value+percent', textposition='inside')
st.plotly_chart(fig_codes, use_container_width=True)
