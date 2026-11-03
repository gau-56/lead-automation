import pandas as pd
import plotly.express as px
import streamlit as st

from app.db import get_conn, init_db

st.set_page_config(page_title="Leads Dashboard", layout="wide")
init_db()

STATUSES = ["new", "contacted", "won", "lost"]


@st.cache_data(ttl=5)
def load_leads():
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM leads ORDER BY id DESC", conn)


st.title("Leads Dashboard")
st.caption("New enquiries, scored and summarized automatically.")

if st.button("Refresh"):
    st.cache_data.clear()

df = load_leads()

if df.empty:
    st.info("No leads yet. Open http://127.0.0.1:8000 and submit a test enquiry.")
    st.stop()

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total leads", len(df))
c2.metric("Hot", int((df["score"] == "hot").sum()))
c3.metric("New (unanswered)", int((df["status"] == "new").sum()))
c4.metric("Won", int((df["status"] == "won").sum()))

# ---------- Filters ----------
f1, f2 = st.columns(2)
score_filter = f1.multiselect("Score", ["hot", "warm", "cold"], default=["hot", "warm", "cold"])
status_filter = f2.multiselect("Status", STATUSES, default=STATUSES)

filtered = df[df["score"].isin(score_filter) & df["status"].isin(status_filter)]

left, right = st.columns([2, 1])

with left:
    st.subheader("All leads")
    st.dataframe(
        filtered[["id", "created_at", "name", "score", "category", "summary", "status"]],
        use_container_width=True,
        hide_index=True,
    )

with right:
    counts = df["score"].value_counts().reset_index()
    counts.columns = ["score", "count"]
    st.plotly_chart(
        px.pie(counts, names="score", values="count", title="Leads by score"),
        use_container_width=True,
    )

# ---------- Lead detail ----------
st.subheader("Lead detail")
if filtered.empty:
    st.warning("No leads match these filters.")
    st.stop()

lead_id = st.selectbox(
    "Select a lead",
    filtered["id"],
    format_func=lambda i: f"#{i} - {filtered.loc[filtered['id'] == i, 'name'].iloc[0]}",
)
lead = filtered[filtered["id"] == lead_id].iloc[0]

d1, d2 = st.columns(2)
with d1:
    st.write(f"**Name:** {lead['name']}")
    st.write(f"**Email:** {lead['email']}")
    st.write(f"**Phone:** {lead['phone'] or '-'}")
    st.write(f"**Score:** {lead['score']}  |  **Category:** {lead['category']}")
    st.write("**Original message:**")
    st.text(lead["message"])

with d2:
    st.write("**Suggested reply (review before sending):**")
    st.text(lead["suggested_reply"])
    new_status = st.selectbox("Status", STATUSES, index=STATUSES.index(lead["status"]))
    if st.button("Update status"):
        with get_conn() as conn:
            conn.execute("UPDATE leads SET status = ? WHERE id = ?", (new_status, int(lead_id)))
        st.cache_data.clear()
        st.success("Status updated.")
        st.rerun()