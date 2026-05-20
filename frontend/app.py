import streamlit as st
import httpx

st.set_page_config(page_title="Multi-Agent Code Generation", layout="wide")
st.markdown("""
<style>
body, .stApp { background-color: #0e1117; color: #f0f2f6; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Multi-Agent Code Generation + Automated Testing")
prompt = st.text_area("Enter software prompt", height=200)
retries = st.slider("Max retries", 1, 10, 3)

if st.button("Run Workflow"):
    with st.spinner("Running agents..."):
        resp = httpx.post("http://localhost:8000/api/run", json={"prompt": prompt, "max_retries": retries}, timeout=300)
    if resp.status_code == 200:
        data = resp.json()
        st.success(f"Session {data['session_id']} complete. Passed: {data['tests_passed']}")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Generated Code")
            st.code(data["code"], language="python")
            st.download_button("Download code", data["code"], file_name="main.py")
        with col2:
            st.subheader("Generated Tests")
            st.code(data["tests"], language="python")
            st.download_button("Download tests", data["tests"], file_name="test_main.py")
        st.subheader("Execution Logs")
        st.text(data["logs"])
        st.subheader("Agent Timeline")
        for event in data["events"]:
            st.write(f"**{event['agent']}**: {event['message']}")
        st.metric("Coverage", data["coverage"])
        st.metric("Quality Score", data["quality_score"])
    else:
        st.error(resp.text)
