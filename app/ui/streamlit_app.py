import streamlit as st
import requests
import threading
import queue
import time
import random
from datetime import datetime

# Import centralized settings
from app.core.config import settings

# -----------------------------
# Config
# -----------------------------
FASTAPI_URL = settings.BACKEND_URL
NUM_PROMPTS = 20
DONE_TOKEN = "__DONE__"

st.set_page_config(page_title="Streaming LLM Demo", layout="wide", page_icon="⚡")

# -----------------------------
# Custom CSS for Aesthetic Borders & Cards
# -----------------------------
st.markdown("""
<style>
    /* Card Container Styling */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #e5e7eb;
        padding: 1rem;
        transition: transform 0.2s;
    }

    /* Header Typography */
    h1 { font-family: 'Inter', sans-serif; font-weight: 700; color: #111827; }
    h2, h3 { font-family: 'Inter', sans-serif; color: #374151; }

    /* Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .status-waiting { background-color: #f3f4f6; color: #6b7280; border: 1px solid #e5e7eb; }
    .status-running { background-color: #eff6ff; color: #3b82f6; border: 1px solid #bfdbfe; }
    .status-done { background-color: #ecfdf5; color: #10b981; border: 1px solid #a7f3d0; }

    /* Time Badge */
    .time-badge {
        font-family: monospace;
        font-size: 0.8rem;
        color: #6b7280;
        margin-left: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ High-Throughput Streamer")
st.caption("Concurrent Streaming • Latency Tracking")

# -----------------------------
# Session State Initialization
# -----------------------------
if "queues" not in st.session_state:
    st.session_state.queues = [queue.Queue() for _ in range(NUM_PROMPTS)]

# Store text output
if "outputs" not in st.session_state:
    st.session_state.outputs = [""] * NUM_PROMPTS

# Store completion status
if "done" not in st.session_state:
    st.session_state.done = [False] * NUM_PROMPTS

# Store timings
if "start_time" not in st.session_state:
    st.session_state.start_time = 0.0
if "durations" not in st.session_state:
    st.session_state.durations = [0.0] * NUM_PROMPTS

if "started" not in st.session_state:
    st.session_state.started = False


# -----------------------------
# Backend Logic
# -----------------------------
def stream_response(prompt: str):
    """Generates streaming tokens. Replaces API call with simulation if needed."""
    try:
        # REAL API CALL
        with requests.post(
                FASTAPI_URL,
                json={"prompt": prompt},
                stream=True,
                timeout=5,  # Fail fast to switch to simulation for demo
        ) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=None):
                if chunk:
                    yield chunk.decode("utf-8", errors="ignore")
    except Exception as e:
        # SIMULATION (For demo reliability)
        yield f"[Simulating due to connection error: {e}] "
        dummy_text = "Analysis complete. The system is functioning within normal parameters. We have observed optimal throughput. " * 3
        tokens = dummy_text.split(" ")
        for token in tokens:
            time.sleep(random.uniform(0.01, 0.05))  # Random jitter
            yield token + " "


def worker(prompt, q: queue.Queue):
    try:
        for token in stream_response(prompt):
            q.put(token)
    except Exception as e:
        q.put(f"\n❌ {e}")
    finally:
        q.put(DONE_TOKEN)


# -----------------------------
# UI: Inputs Area
# -----------------------------
with st.expander("Control Panel & Prompts", expanded=not st.session_state.started):
    col_tools1, col_tools2 = st.columns([1, 5])

    with col_tools1:
        if st.button("🎲 Randomize", type="secondary", use_container_width=True):
            defaults = [
                "hi",
                "how are you?",
                "what you do?",
                "who are you?",
                "what is your purpose?",

                "Define 'Epistemology' in very short",
                "Explain entropy in one line",
                "What is artificial intelligence in one sentence?",
                "Define recursion in simple words",

                "Why is the sky blue? (short)",
                "What is the difference between knowledge and belief?",
                "Can something be true but not provable?",
                "Is time an illusion? Answer briefly",

                "short joke about recursion",
                "Tell a one-line programming joke",
                "Explain AI like I am five",
                "Write a haiku about code",

                "What is a neural network?",
                "Difference between CPU and GPU in one line",
                "What is overfitting in machine learning?",
                "What does 'RAG' mean in AI?",

                "What is Python used for?",
                "Explain REST API in one line",
                "What is a thread?",
                "What is concurrency vs parallelism?",

                "If all bloops are razzies and all razzies are lazzies, are all bloops lazzies?",
                "What comes next: 2, 4, 8, 16, ?",
                "Is zero even or odd?",

                "Is AI good or bad?",
                "Will AI replace programmers?",
                "Is learning to code still worth it?"
            ]

            for i in range(NUM_PROMPTS):
                st.session_state[f"prompt_{i}"] = defaults[i % len(defaults)]

    # Grid for inputs
    cols = st.columns(4)
    prompts = []
    for i in range(NUM_PROMPTS):
        with cols[i % 4]:
            prompts.append(st.text_area(
                f"Prompt {i + 1}",
                key=f"prompt_{i}",
                height=70,
                placeholder="Enter prompt...",
                label_visibility="collapsed"
            ))

# -----------------------------
# Action
# -----------------------------
if st.button("Launch Generation", type="primary"):
    # Reset State
    st.session_state.started = True
    st.session_state.outputs = [""] * NUM_PROMPTS
    st.session_state.done = [False] * NUM_PROMPTS
    st.session_state.durations = [0.0] * NUM_PROMPTS
    st.session_state.queues = [queue.Queue() for _ in range(NUM_PROMPTS)]

    # Set Start Time
    st.session_state.start_time = time.time()

    # Launch Threads
    for i in range(NUM_PROMPTS):
        p_text = prompts[i].strip()
        if p_text:
            threading.Thread(
                target=worker,
                args=(p_text, st.session_state.queues[i]),
                daemon=True,
            ).start()
        else:
            st.session_state.done[i] = True

# -----------------------------
# UI: Output Grid
# -----------------------------
if st.session_state.started:
    st.markdown("### 📡 Live Feed")

    # 2-Column Grid for Results
    grid_cols = st.columns(2)
    placeholders = []

    # initialize placeholders
    for i in range(NUM_PROMPTS):
        with grid_cols[i % 2]:
            # The 'border=True' here combined with custom CSS creates the card look
            with st.container(border=True):
                # Header: Title + Badge + Timer
                header_col, status_col = st.columns([7, 3])

                with header_col:
                    st.markdown(f"**#{i + 1}** _{prompts[i][:35]}..._")

                with status_col:
                    status_ph = st.empty()

                st.divider()

                # Content Body
                text_ph = st.empty()
                placeholders.append({
                    "text": text_ph,
                    "status": status_ph,
                    "idx": i
                })

    # -----------------------------
    # Event Loop
    # -----------------------------
    all_done = False
    while not all_done:
        all_done = True
        current_time = time.time()

        for i in range(NUM_PROMPTS):
            # 1. Process Queue
            q = st.session_state.queues[i]
            while not q.empty():
                item = q.get()
                if item == DONE_TOKEN:
                    st.session_state.done[i] = True
                    # Calculate final duration only once
                    if st.session_state.durations[i] == 0.0:
                        st.session_state.durations[i] = time.time() - st.session_state.start_time
                else:
                    st.session_state.outputs[i] += item

            # 2. Update Text
            ph = placeholders[i]
            content = st.session_state.outputs[i]
            ph["text"].markdown(content if content else "...")

            # 3. Update Status & Timer
            if st.session_state.done[i]:
                # Finished State
                final_time = st.session_state.durations[i]
                ph["status"].markdown(
                    f'''<div style="text-align:right">
                        <span class="status-badge status-done">Done</span>
                        <span class="time-badge">{final_time:.2f}s</span>
                    </div>''',
                    unsafe_allow_html=True
                )
            else:
                # Running State
                elapsed = current_time - st.session_state.start_time
                ph["status"].markdown(
                    f'''<div style="text-align:right">
                        <span class="status-badge status-running">Run</span>
                        <span class="time-badge">{elapsed:.1f}s</span>
                    </div>''',
                    unsafe_allow_html=True
                )
                all_done = False

        if not all_done:
            time.sleep(0.05)
