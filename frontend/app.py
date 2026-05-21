import io
import json
import time
from datetime import datetime
from typing import Any

import httpx
import streamlit as st

API_BASE_URL = "http://localhost:8000/api"
REQUEST_TIMEOUT_SECONDS = 600

st.set_page_config(
    page_title="Multi-Agent AI Coding Console",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_state() -> None:
    defaults = {
        "current_run": None,
        "local_history": [],
        "is_running": False,
        "last_error": None,
        "activity_feed": [],
        "live_logs": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()

st.markdown(
    """
<style>
:root {
  --bg: #0b1020;
  --card: #121a30;
  --card-soft: #192542;
  --text: #e7ecff;
  --muted: #9fb0dc;
  --accent: #7c9cff;
  --success: #36d399;
  --error: #ff6b6b;
}

.stApp {
  background: radial-gradient(1200px 700px at 20% -10%, #1b2850, var(--bg));
  color: var(--text);
}

.block-container {
  padding-top: 1.25rem;
}

.card {
  background: rgba(18, 26, 48, 0.88);
  border: 1px solid rgba(124, 156, 255, 0.22);
  border-radius: 14px;
  padding: 1rem 1.1rem;
  box-shadow: 0 10px 25px rgba(3, 8, 20, 0.35);
}

.metric {
  background: rgba(25, 37, 66, 0.7);
  border-radius: 10px;
  padding: .8rem;
  border: 1px solid rgba(159, 176, 220, 0.2);
}

.small-muted { color: var(--muted); font-size: .9rem; }
</style>
""",
    unsafe_allow_html=True,
)


def fetch_session_history() -> list[dict[str, Any]]:
    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(f"{API_BASE_URL}/sessions")
            response.raise_for_status()
            return response.json()
    except Exception:
        return []


def run_workflow(prompt: str, max_retries: int) -> dict[str, Any] | None:
    st.session_state.is_running = True
    st.session_state.last_error = None
    st.session_state.activity_feed = []
    st.session_state.live_logs = ""

    activity_placeholder = st.empty()
    logs_placeholder = st.empty()

    planned_steps = [
        "Planning agent workflow",
        "Generating candidate solution",
        "Synthesizing unit tests",
        "Running automated tests",
        "Evaluating quality and retries",
    ]

    try:
        for idx, step in enumerate(planned_steps, start=1):
            st.session_state.activity_feed.append({"agent": "system", "message": step})
            activity_placeholder.markdown(
                "\n".join([f"- `{entry['agent']}` · {entry['message']}" for entry in st.session_state.activity_feed])
            )
            st.session_state.live_logs += f"[{datetime.utcnow().isoformat()}] {step}...\n"
            logs_placeholder.code(st.session_state.live_logs, language="bash")
            time.sleep(0.22)

        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = client.post(
                f"{API_BASE_URL}/run",
                json={"prompt": prompt, "max_retries": max_retries},
            )
            response.raise_for_status()
            result = response.json()

        st.session_state.current_run = result
        st.session_state.local_history.insert(0, {
            "session_id": result["session_id"],
            "status": result["status"],
            "tests_passed": result["tests_passed"],
            "created_at": datetime.utcnow().isoformat(),
        })
        return result
    except httpx.HTTPStatusError as exc:
        st.session_state.last_error = f"Backend error: {exc.response.text}"
    except Exception as exc:
        st.session_state.last_error = f"Request failed: {exc}"
    finally:
        st.session_state.is_running = False

    return None


st.title("🧠 Multi-Agent AI Coding System")
st.caption("Modern Streamlit console with execution telemetry, logs, artifacts, and session history.")

with st.sidebar:
    st.markdown("### ⚙️ Run Configuration")
    max_retries = st.slider("Max retries", min_value=1, max_value=10, value=3)
    st.markdown("### 🗂 Session History")
    remote_history = fetch_session_history()

    if remote_history:
        for item in remote_history[:12]:
            icon = "✅" if item.get("passed") else "❌"
            st.markdown(
                f"{icon} **Session {item['id']}**  \\n<span class='small-muted'>Status: {item['status']} · {item['created_at']}</span>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No session history available yet.")

left, right = st.columns([1.15, 1], gap="large")

with left:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Prompt Input")
    prompt = st.text_area(
        "Describe the software you want to generate",
        placeholder="Example: Build a FastAPI service with JWT auth, SQLAlchemy models, and tests...",
        height=220,
    )

    run_disabled = st.session_state.is_running or len(prompt.strip()) < 5
    if st.button("🚀 Run Multi-Agent Workflow", disabled=run_disabled, use_container_width=True):
        run_workflow(prompt=prompt, max_retries=max_retries)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Live Agent Activity Feed")
    if st.session_state.activity_feed:
        for event in st.session_state.activity_feed:
            st.markdown(f"- **{event['agent']}** · {event['message']}")
    else:
        st.caption("Activity feed will appear during execution.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Real-Time Logs")
    if st.session_state.live_logs:
        st.code(st.session_state.live_logs, language="bash")
    else:
        st.caption("Runtime logs will stream here while the workflow is executing.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    result = st.session_state.current_run
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Execution Summary")
    if result:
        c1, c2, c3 = st.columns(3)
        c1.metric("Session", result["session_id"])
        c2.metric("Coverage", result["coverage"])
        c3.metric("Quality", f"{result['quality_score']:.2f}")

        retry_pct = min(1.0, result["retries_used"] / max_retries)
        st.markdown("**Retry Visualization**")
        st.progress(retry_pct, text=f"Retries used: {result['retries_used']} / {max_retries}")

        if result["tests_passed"]:
            st.success("All tests passed.")
        else:
            st.warning("Tests did not pass successfully.")
    else:
        st.caption("Run a workflow to view generated outputs and metrics.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Generated Code")
    if result:
        st.code(result["code"], language="python")
        zip_buffer = io.BytesIO()
        zip_payload = {
            "main.py": result["code"],
            "test_main.py": result["tests"],
            "logs.txt": result["logs"],
            "events.json": json.dumps(result["events"], indent=2),
        }
        st.download_button(
            "⬇️ Download code bundle",
            data=json.dumps(zip_payload, indent=2),
            file_name=f"session_{result['session_id']}_artifacts.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.caption("Generated code will appear here.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Test Results")
    if result:
        st.code(result["tests"], language="python")
        st.text_area("Execution Logs", value=result["logs"], height=180, disabled=True)
        st.markdown("**Agent Timeline**")
        for event in result["events"]:
            st.write(f"- `{event['agent']}` · {event['message']}")
    else:
        st.caption("Test artifacts and logs will appear here.")
    st.markdown("</div>", unsafe_allow_html=True)
