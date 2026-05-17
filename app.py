import streamlit as st
from dotenv import load_dotenv
from graph import graph
from database import init_db, get_all_claims
from state import GraphState

load_dotenv()
init_db()

st.set_page_config(page_title="Sentinels of Truth", layout="wide")
st.title("🛡️ Sentinels of Truth – Multi-Agent Fact Checker")

with st.sidebar:
    st.header("📜 Verified Claims Database")
    claims = get_all_claims()
    if claims:
        for claim, verdict, ts in claims[:10]:
            st.markdown(f"**{claim}**  \n→ *{verdict}*  \n`{ts[:10]}`")
            st.divider()
    else:
        st.info("No claims verified yet.")

col1, col2 = st.columns([2, 1])

with col1:
    user_claim = st.text_area(
        "Enter a claim to verify",
        height=150,
        placeholder="Example: 'India's GDP growth exceeded 8% in the last quarter.'"
    )
    if st.button("🔍 Verify Claim", type="primary"):
        if not user_claim.strip():
            st.warning("Please enter a claim.")
        else:
            # Initialize the LangGraph state
            initial_state: GraphState = {
                "original_claim": user_claim,
                "verification_report": None,
                "db_action": "",
                "human_review_needed": False,
                "error_message": None,
            }

            with st.spinner("Agents are investigating..."):
                final_state = graph.invoke(initial_state)

            # Display results
            report = final_state["verification_report"]
            action = final_state["db_action"]

            st.subheader("📋 Verification Report")
            if report:
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Verdict", report.verdict)
                col_b.metric("Confidence", f"{report.confidence:.0%}")
                col_c.metric("Database Action", action)

                st.markdown("**Evidence Summary:**")
                st.info(report.evidence_summary)

                with st.expander("🔗 Sources Consulted"):
                    for src in report.sources:
                        st.markdown(f"- [{src}]({src})")

                if final_state["human_review_needed"]:
                    st.error(
                        "⚠️ **Contradiction detected!** This claim conflicts with "
                        "an existing verified claim. Human review required."
                    )
            else:
                st.error("Investigation failed. Please try again.")

with col2:
    st.subheader("🧠 Agent Workflow")
    st.markdown("""
    **1. Agent Alpha (Investigator)**  
    → Searches the web using Tavily  
    → Produces a structured verification report  

    **2. Agent Beta (Archivist)**  
    → Queries the SQLite database  
    → Inserts / Flags / Discards accordingly  

    **Real‑time database updates** are shown in the sidebar.
    """)

# Refresh the side bar automatically after each run
if "rerun" not in st.session_state:
    st.session_state.rerun = False
if st.button("🔄 Refresh Database View"):
    st.rerun()