import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from pathlib import Path
import base64
import sqlite3
from datetime import datetime

st.set_page_config(
    page_title="MP Fund Analytics Dashboard",
    page_icon="🇮🇳",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "cleaned_workfile.csv"
CONSTITUTION_IMAGE = BASE_DIR / "assets" / "constitution.png"
FEEDBACK_DB = BASE_DIR / "feedback.db"

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


def init_feedback_db():
    """Create the local feedback store and seed it for the prototype."""
    seed_feedback = [
        ("2026-08-24 10:15", 5, "Dashboard clarity", "The state-wise map makes it very easy to understand where MP funds are allocated.", "Priya, Delhi"),
        ("2026-08-25 14:40", 4, "Data access", "Downloading the filtered data will be useful for students and local community groups.", "Arjun, Pune"),
        ("2026-08-27 09:05", 5, "Usability", "I could filter my state and find the relevant constituency in just a few clicks.", "Meera, Bengaluru"),
        ("2026-08-29 16:20", 4, "Feature request", "It would be helpful to see the allocation trend for each year in a future update.", "Rahul, Lucknow"),
    ]

    with sqlite3.connect(FEEDBACK_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submitted_at TEXT NOT NULL,
                rating INTEGER NOT NULL,
                category TEXT NOT NULL,
                comment TEXT NOT NULL,
                name TEXT
            )
            """
        )
        existing_count = conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        if existing_count == 0:
            conn.executemany(
                """
                INSERT INTO feedback (submitted_at, rating, category, comment, name)
                VALUES (?, ?, ?, ?, ?)
                """,
                seed_feedback,
            )


def load_feedback():
    with sqlite3.connect(FEEDBACK_DB) as conn:
        return pd.read_sql_query(
            """
            SELECT submitted_at, rating, category, comment, name
            FROM feedback
            ORDER BY id DESC
            """,
            conn,
        )


def save_feedback(rating, category, comment, name):
    with sqlite3.connect(FEEDBACK_DB) as conn:
        conn.execute(
            """
            INSERT INTO feedback (submitted_at, rating, category, comment, name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                rating,
                category,
                comment.strip(),
                name.strip() or "Anonymous citizen",
            ),
        )

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
    top: 0; left: 0;
    width: 100%; height: 7px;
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

h1 {{ font-size: 44px !important; font-weight: 800 !important; }}
h2, h3 {{ font-weight: 750 !important; }}

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

    required = [STATE_COL, MP_COL, CONSTITUENCY_COL, FUND_COL]
    missing = [c for c in required if c not in data.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.write("Available columns:", list(data.columns))
        st.stop()

    data[FUND_COL] = (
        data[FUND_COL].astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("Rs.", "", regex=False)
        .str.strip()
    )
    data[FUND_COL] = pd.to_numeric(data[FUND_COL], errors="coerce").fillna(0)

    for col in [STATE_COL, MP_COL, CONSTITUENCY_COL]:
        data[col] = data[col].fillna("Unknown").astype(str).str.strip()

    return data

df = load_data()
init_feedback_db()

def crore(value):
    return value / 10_000_000

def money_cr(value):
    return f"₹{crore(value):,.2f} Cr"

def horizontal_chart(series, title, xlabel):
    series = series.head(10).sort_values()
    fig, ax = plt.subplots(figsize=(12, 6))

    if series.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.axis("off")
        return fig

    bars = ax.barh(series.index.astype(str), series.values)
    ax.set_title(title, fontsize=17, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)

    maximum = max(series.values)
    ax.set_xlim(0, maximum * 1.18 if maximum else 1)

    for bar, value in zip(bars, series.values):
        ax.text(
            bar.get_width() + maximum * 0.01,
            bar.get_y() + bar.get_height()/2,
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
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.axis("off")
        return fig

    bars = ax.bar(series.index.astype(str), series.values)
    ax.set_title(title, fontsize=17, fontweight="bold")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", rotation=45, labelsize=9)

    maximum = max(series.values)
    ax.set_ylim(0, maximum * 1.18 if maximum else 1)

    for bar, value in zip(bars, series.values):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + maximum * 0.015,
            f"{value:,.2f}",
            ha="center", va="bottom", fontsize=8
        )

    fig.tight_layout()
    return fig

st.title("🇮🇳 MP Fund Analytics Dashboard")
st.caption("Data-driven analysis of Member of Parliament Fund Allocation across India")
st.divider()

st.sidebar.header("🔎 Dashboard Filters")

states = sorted(df[STATE_COL].unique().tolist())
selected_states = st.sidebar.multiselect(
    "🗺️ Select State", states, placeholder="Choose states"
)

available_mps = (
    sorted(df.loc[df[STATE_COL].isin(selected_states), MP_COL].unique().tolist())
    if selected_states else sorted(df[MP_COL].unique().tolist())
)

selected_mps = st.sidebar.multiselect(
    "👤 Select MP", available_mps, placeholder="Choose MPs"
)

if st.sidebar.button("🔄 Reset Filters", use_container_width=True):
    st.rerun()

filtered = df.copy()

if selected_states:
    filtered = filtered[filtered[STATE_COL].isin(selected_states)]

if selected_mps:
    filtered = filtered[filtered[MP_COL].isin(selected_mps)]

st.subheader("📌 Project Summary")

total_fund = filtered[FUND_COL].sum()
total_mps = filtered[MP_COL].nunique()
total_states = filtered[STATE_COL].nunique()
total_constituencies = filtered[CONSTITUENCY_COL].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Total Allocated Fund", f"₹{crore(total_fund):,.2f} Cr")
c2.metric("👥 Total MPs", f"{total_mps:,}")
c3.metric("🗺️ Total States", f"{total_states:,}")
c4.metric("📍 Constituencies", f"{total_constituencies:,}")

st.divider()

st.subheader("💡 Key Insights")

if filtered.empty:
    st.warning("No records found for the selected filters.")
else:
    state_funds = filtered.groupby(STATE_COL)[FUND_COL].sum().sort_values(ascending=False)
    constituency_funds = filtered.groupby([STATE_COL, CONSTITUENCY_COL])[FUND_COL].sum().sort_values(ascending=False)
    mp_funds = filtered.groupby(MP_COL)[FUND_COL].sum().sort_values(ascending=False)

    a, b, c = st.columns(3)

    with a:
        st.info(f"🏆 **Highest Funded State**\n\n### {state_funds.index[0]}\n\n{money_cr(state_funds.iloc[0])}")

    with b:
        st.success(
            f"📍 **Highest Funded Constituency**\n\n"
            f"### {constituency_funds.index[0][1]}\n\n"
            f"{money_cr(constituency_funds.iloc[0])}\n\n"
            f"**State:** {constituency_funds.index[0][0]}"
        )

    with c:
        st.warning(f"👤 **Highest Funded MP**\n\n### {mp_funds.index[0]}\n\n{money_cr(mp_funds.iloc[0])}")

st.divider()

st.subheader("📊 Top 10 States by Allocated Fund")
top_states = filtered.groupby(STATE_COL)[FUND_COL].sum().sort_values(ascending=False) / 10_000_000
fig = vertical_chart(top_states, "Top 10 States by Allocated Fund", "Allocated Fund (₹ Crore)")
st.pyplot(fig, use_container_width=True)
plt.close(fig)

st.divider()

st.subheader("👥 Top 10 MPs by Allocated Fund")
top_mps = filtered.groupby(MP_COL)[FUND_COL].sum().sort_values(ascending=False) / 10_000_000
fig = horizontal_chart(top_mps, "Top 10 MPs by Allocated Fund", "Allocated Fund (₹ Crore)")
st.pyplot(fig, use_container_width=True)
plt.close(fig)

st.divider()

st.subheader("🗺️ Top 10 States by Number of MPs")
state_mp_count = filtered.groupby(STATE_COL)[MP_COL].nunique().sort_values(ascending=False)
fig = vertical_chart(state_mp_count, "Top 10 States by Number of MPs", "Number of MPs")
st.pyplot(fig, use_container_width=True)
plt.close(fig)

st.divider()

st.subheader("📍 Top 10 Constituencies by Allocated Fund")
top_constituencies = filtered.groupby(CONSTITUENCY_COL)[FUND_COL].sum().sort_values(ascending=False) / 10_000_000
fig = horizontal_chart(top_constituencies, "Top 10 Constituencies by Allocated Fund", "Allocated Fund (₹ Crore)")
st.pyplot(fig, use_container_width=True)
plt.close(fig)

st.divider()

st.subheader("🇮🇳 Interactive India State-wise Fund Map")
st.caption("Hover over a state to view its allocated fund, MPs and constituencies.")

map_data = (
    filtered.groupby(STATE_COL)
    .agg(
        Allocated_Fund=(FUND_COL, "sum"),
        MPs=(MP_COL, "nunique"),
        Constituencies=(CONSTITUENCY_COL, "nunique")
    )
    .reset_index()
)

map_data["Allocated_Fund_Crore"] = (map_data["Allocated_Fund"] / 10_000_000).round(2)

GEOJSON_URL = "https://raw.githubusercontent.com/geohacker/india/master/state/india_state.geojson"

if not map_data.empty:
    try:
        fig_map = px.choropleth(
            map_data,
            geojson=GEOJSON_URL,
            featureidkey="properties.NAME_1",
            locations=STATE_COL,
            color="Allocated_Fund_Crore",
            color_continuous_scale="Viridis",
            hover_name=STATE_COL,
            hover_data={
                "Allocated_Fund_Crore": ":.2f",
                "MPs": True,
                "Constituencies": True
            },
            labels={
                "Allocated_Fund_Crore": "Fund (₹ Crore)",
                "MPs": "MPs",
                "Constituencies": "Constituencies"
            }
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.update_layout(height=650, margin=dict(l=0, r=0, t=20, b=0))
        st.plotly_chart(fig_map, use_container_width=True)
    except Exception as e:
        st.warning("The map could not be loaded. The dashboard is still working.")
        st.caption(str(e))
        st.dataframe(map_data, use_container_width=True, hide_index=True)
else:
    st.info("No map data available.")

st.divider()

st.subheader("📈 Fund Distribution Analysis")

x1, x2, x3 = st.columns(3)
x1.metric("💰 Average Fund / MP", f"₹{crore(total_fund/total_mps) if total_mps else 0:,.2f} Cr")
x2.metric("📍 Average Fund / Constituency", f"₹{crore(total_fund/total_constituencies) if total_constituencies else 0:,.2f} Cr")
x3.metric("📋 Total Records", f"{len(filtered):,}")

st.divider()

st.subheader("📋 Filtered Dataset")
st.write(f"Showing **{len(filtered):,}** records")
st.dataframe(filtered, use_container_width=True, hide_index=True)

st.divider()

st.subheader("⬇️ Download Filtered Data")
st.download_button(
    "📥 Download CSV",
    data=filtered.to_csv(index=False),
    file_name="filtered_mp_fund_data.csv",
    mime="text/csv"
)

st.divider()

st.subheader("ℹ️ About This Dashboard")
st.markdown("""
**MP Fund Analytics Dashboard**

This dashboard provides an interactive view of MP fund allocation across India.

**Technology Used:** Python, Pandas, Streamlit, Matplotlib and Plotly.
""")

st.divider()

st.subheader("💬 Citizen Feedback")
st.caption(
    "Your feedback helps us make fund information easier for every citizen to explore. "
    "Responses are saved locally for this prototype."
)

if st.session_state.get("feedback_success"):
    st.success(st.session_state.pop("feedback_success"))

feedback_df = load_feedback()
feedback_count = len(feedback_df)
average_rating = feedback_df["rating"].mean() if feedback_count else 0
positive_share = (
    (feedback_df["rating"] >= 4).mean() * 100 if feedback_count else 0
)

f1, f2, f3 = st.columns(3)
f1.metric("Community responses", feedback_count)
f2.metric("Average rating", f"{average_rating:.1f} / 5")
f3.metric("Positive feedback", f"{positive_share:.0f}%")

st.markdown("#### What citizens are saying")
for _, item in feedback_df.head(3).iterrows():
    with st.container(border=True):
        st.markdown(
            f"**{'★' * int(item['rating'])}{'☆' * (5 - int(item['rating']))} "
            f"· {item['category']}**"
        )
        st.write(item["comment"])
        st.caption(f"{item['name']} · {item['submitted_at']}")

with st.expander("How feedback is used"):
    st.write(
        "Feedback highlights what citizens find clear, what data they need next, and "
        "which dashboard improvements should be prioritised."
    )

st.markdown("#### Share your feedback")
with st.form("citizen_feedback_form", clear_on_submit=True):
    form_left, form_right = st.columns(2)
    with form_left:
        rating = st.slider("Overall experience", min_value=1, max_value=5, value=5)
        category = st.selectbox(
            "Feedback topic",
            ["Dashboard clarity", "Data access", "Usability", "Feature request", "Other"],
        )
    with form_right:
        name = st.text_input("Name and city (optional)", placeholder="e.g. Asha, Bhopal")
        comment = st.text_area(
            "Your feedback",
            placeholder="Tell us what worked well or what we can improve.",
            max_chars=500,
        )

    feedback_submitted = st.form_submit_button("Submit feedback", use_container_width=True)

if feedback_submitted:
    if len(comment.strip()) < 8:
        st.warning("Please add a short comment of at least 8 characters.")
    else:
        save_feedback(rating, category, comment, name)
        st.session_state["feedback_success"] = "Thank you. Your feedback has been recorded."
        st.rerun()

st.divider()
st.caption("🇮🇳 MP Fund Analytics Dashboard | Data Analysis & Visualization Project")
st.markdown('<div class="watermark">WE, THE PEOPLE OF INDIA</div>', unsafe_allow_html=True)
