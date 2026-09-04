
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import base64

st.set_page_config(
    page_title="MP Fund Analytics Dashboard",
    page_icon="🇮🇳",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "cleaned_workfile.csv"
CONSTITUTION_IMAGE = BASE_DIR / "assets" / "constitution.png"

FUND_COL = "Allocated AMOUNT ( ₹ )"
MP_COL = "Hon'ble Members of Parliaments"
STATE_COL = "State"
CONSTITUENCY_COL = "Constituency"


def image_base64(path):
    if not path.exists():
        return None
    try:
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    except Exception:
        return None


img = image_base64(CONSTITUTION_IMAGE)

if img:
    bg = f"""
    .stApp {{
        background-image:
            linear-gradient(rgba(7,12,22,0.95), rgba(7,12,22,0.97)),
            url("data:image/png;base64,{img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    """
else:
    bg = """
    .stApp {
        background: linear-gradient(rgba(7,12,22,0.98), rgba(7,12,22,0.98));
    }
    """


st.markdown(f"""
<style>
{bg}

.stApp::before {{
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 7px;
    background: linear-gradient(
        to right,
        #FF9933 0%, #FF9933 33.33%,
        #FFFFFF 33.33%, #FFFFFF 66.66%,
        #138808 66.66%, #138808 100%
    );
    z-index: 999999;
}}

.main .block-container {{
    max-width: 1450px;
    padding-top: 45px;
    padding-bottom: 50px;
}}

h1 {{
    font-size: 44px !important;
    font-weight: 800 !important;
}}

h2, h3 {{
    font-weight: 750 !important;
}}

[data-testid="stMetric"] {{
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 15px;
    padding: 18px;
}}

.watermark {{
    position: fixed;
    bottom: 18px;
    right: 25px;
    opacity: 0.06;
    font-size: 42px;
    font-weight: bold;
    color: white;
    pointer-events: none;
    z-index: 0;
}}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():

    if not CSV_FILE.exists():
        st.error("cleaned_workfile.csv was not found.")
        st.stop()

    data = pd.read_csv(CSV_FILE)

    data.columns = data.columns.astype(str).str.strip()

    required = [
        STATE_COL,
        MP_COL,
        CONSTITUENCY_COL,
        FUND_COL
    ]

    missing = [
        c for c in required
        if c not in data.columns
    ]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.write("Available columns:", list(data.columns))
        st.stop()

    data[FUND_COL] = (
        data[FUND_COL]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("Rs.", "", regex=False)
        .str.strip()
    )

    data[FUND_COL] = pd.to_numeric(
        data[FUND_COL],
        errors="coerce"
    ).fillna(0)

    for col in [
        STATE_COL,
        MP_COL,
        CONSTITUENCY_COL
    ]:
        data[col] = (
            data[col]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
        )

    return data


df = load_data()


def crore(value):
    return value / 10_000_000


def money_cr(value):
    return f"₹{crore(value):,.2f} Cr"


def horizontal_chart(series, title, xlabel):

    series = series.head(10).sort_values()

    fig, ax = plt.subplots(figsize=(12, 6))

    if series.empty:
        ax.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center"
        )
        ax.axis("off")
        return fig

    bars = ax.barh(
        series.index.astype(str),
        series.values
    )

    ax.set_title(
        title,
        fontsize=17,
        fontweight="bold"
    )

    ax.set_xlabel(xlabel)

    ax.grid(
        axis="x",
        alpha=0.25
    )

    ax.set_axisbelow(True)

    maximum = max(series.values)

    ax.set_xlim(
        0,
        maximum * 1.18 if maximum else 1
    )

    for bar, value in zip(
        bars,
        series.values
    ):
        ax.text(
            bar.get_width() + maximum * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,.2f}",
            va="center",
            fontsize=8
        )

    fig.tight_layout()

    return fig


def vertical_chart(series, title, ylabel):

    series = series.head(10)

    fig, ax = plt.subplots(figsize=(12, 6))

    if series.empty:
        ax.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center"
        )

        ax.axis("off")

        return fig

    bars = ax.bar(
        series.index.astype(str),
        series.values
    )

    ax.set_title(
        title,
        fontsize=17,
        fontweight="bold"
    )

    ax.set_ylabel(ylabel)

    ax.grid(
        axis="y",
        alpha=0.25
    )

    ax.set_axisbelow(True)

    ax.tick_params(
        axis="x",
        rotation=45,
        labelsize=9
    )

    maximum = max(series.values)

    ax.set_ylim(
        0,
        maximum * 1.18 if maximum else 1
    )

    for bar, value in zip(
        bars,
        series.values
    ):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + maximum * 0.015,
            f"{value:,.2f}",
            ha="center",
            va="bottom",
            fontsize=8
        )

    fig.tight_layout()

    return fig


# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🇮🇳 MP Fund Analytics Dashboard")

st.caption(
    "Data-driven analysis of Member of Parliament "
   