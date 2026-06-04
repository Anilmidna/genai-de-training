"""
Prompt Engineering for Data Engineers
DevPro Academy
"""

import copy
import time
import json
import re
import streamlit as st
from dotenv import load_dotenv

from helpers import (
    estimate_tokens, fill_template, parse_json_response,
    build_shot_prompt, build_cot_prompt, build_react_prompt,
    build_role_prompt, build_nl_sql_prompt, build_sql_nl_prompt,
    build_json_prompt, build_yaml_prompt, generate_library_md,
    call_claude, call_gemini, call_ollama,
)
from prompts import DE_PROMPTS, ROLES, DEFAULT_SCHEMA

load_dotenv()

st.set_page_config(
    page_title="Prompt Engineering for Data Engineers · DevPro Academy",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Password Gate ─────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("## 🔐 DevPro Academy — Prompt Engineering Lab")
    pwd = st.text_input("Enter access password:", type="password")
    if st.button("Enter"):
        if pwd == st.secrets.get("APP_PASSWORD", ""):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
body, .stMarkdown, .stText { font-size: 16px !important; }
h1 { font-size: 28px !important; }
h2 { font-size: 22px !important; }
h3 { font-size: 19px !important; }

.mission-banner {
    background: linear-gradient(135deg, #1a2f5e 0%, #2563eb 100%);
    border-radius: 14px;
    padding: 22px 28px;
    margin-bottom: 24px;
    color: white;
}
.mission-banner h2 { color: white !important; margin: 0 0 6px 0; font-size: 24px !important; }
.mission-banner .tagline { font-size: 15px; opacity: 0.85; margin-bottom: 12px; }
.mission-banner .learn-tag {
    background: rgba(255,255,255,0.15);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 600;
    display: inline-block;
}

.step-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.step-num {
    background: #2563eb;
    color: white;
    width: 30px; height: 30px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 14px;
    flex-shrink: 0;
}
.step-text { flex: 1; line-height: 1.5; color: #1e293b !important; font-size: 15px; }
.step-text b { color: #1e3a8a !important; }

.prompt-box {
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #1e293b !important;
}
.prompt-system {
    background: #f0fdf4;
    border-left: 5px solid #16a34a;
}
.prompt-user {
    background: #eff6ff;
    border-left: 5px solid #2563eb;
}
.prompt-label {
    font-size: 11px; font-weight: 800; letter-spacing: 1.5px;
    text-transform: uppercase; margin-bottom: 6px;
    font-family: sans-serif;
}
.sys-label { color: #15803d; }
.usr-label { color: #1d4ed8; }

.notice-box {
    background: #fef9c3;
    border: 2px solid #ca8a04;
    border-radius: 10px;
    padding: 14px 18px;
    margin-top: 16px;
    color: #1c1917 !important;
    font-size: 15px;
}
.notice-box b { color: #78350f !important; }

.ollama-pill {
    background: #dcfce7; color: #15803d;
    border: 1px solid #86efac;
    border-radius: 20px; padding: 3px 12px;
    font-size: 12px; font-weight: 700;
    display: inline-block; margin-bottom: 4px;
}
.claude-pill {
    background: #fff7ed; color: #c2410c;
    border: 1px solid #fdba74;
    border-radius: 20px; padding: 3px 12px;
    font-size: 12px; font-weight: 700;
    display: inline-block; margin-bottom: 4px;
}
.gemini-pill {
    background: #eff6ff; color: #1d4ed8;
    border: 1px solid #93c5fd;
    border-radius: 20px; padding: 3px 12px;
    font-size: 12px; font-weight: 700;
    display: inline-block; margin-bottom: 4px;
}
.trainer-only {
    background: #fef2f2;
    border: 2px dashed #f87171;
    border-radius: 12px;
    padding: 28px;
    text-align: center;
}
.concept-box {
    background: #eef2ff;
    border-left: 5px solid #4f46e5;
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1.2rem;
    color: #1e1b4b !important;
    font-size: 15px;
}
.tag-system  { background:#bbf7d0; color:#14532d; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:700; }
.tag-user    { background:#bfdbfe; color:#1e3a5f; padding:3px 10px; border-radius:4px; font-size:12px; font-weight:700; }
.sdk-header  { background:#fff7ed; border:1px solid #fb923c; border-radius:6px; padding:0.5rem 1rem; font-weight:700; color:#7c2d12 !important; }
.lc-header   { background:#f5f3ff; border:1px solid #8b5cf6; border-radius:6px; padding:0.5rem 1rem; font-weight:700; color:#3b0764 !important; }
</style>
""", unsafe_allow_html=True)


# ── Session helpers ────────────────────────────────────────────────────────────
def get_backend() -> str:
    return st.session_state.get("backend", "Gemini")

def get_api_key() -> str:
    return st.session_state.get("api_key", "")

def get_gemini_key() -> str:
    return st.session_state.get("gemini_key", "")

def get_gemini_model() -> str:
    return st.session_state.get("gemini_model", "gemini-3-flash-preview")

def get_claude_model() -> str:
    return st.session_state.get("claude_model", "claude-haiku-4-5-20251001")

def get_ollama_model() -> str:
    return st.session_state.get("ollama_model", "qwen2.5:7b")


# ── UI helpers ─────────────────────────────────────────────────────────────────
def mission_banner(emoji: str, title: str, tagline: str, learn: str):
    st.markdown(f"""
    <div class="mission-banner">
        <h2>{emoji} {title}</h2>
        <div class="tagline">{tagline}</div>
        <span class="learn-tag">🎯 What you'll learn: {learn}</span>
    </div>
    """, unsafe_allow_html=True)


def show_steps(steps: list):
    """steps = list of (bold_title, description) tuples"""
    for i, (title, desc) in enumerate(steps, 1):
        st.markdown(f"""
        <div class="step-row">
            <div class="step-num">{i}</div>
            <div class="step-text"><b>{title}</b> — {desc}</div>
        </div>
        """, unsafe_allow_html=True)


def show_prompt(system: str, user: str):
    """Always-visible prompt display — this IS the learning."""
    st.markdown("**📨 Exact prompt sent to the AI:**")
    st.markdown(f"""
    <div class="prompt-box prompt-system">
        <div class="prompt-label sys-label">🟢 Role (System) — tells the AI WHO it is</div>
        {system.replace(chr(10), '<br>')}
    </div>
    <div class="prompt-box prompt-user">
        <div class="prompt-label usr-label">🔵 Question (User) — the actual request</div>
        {user[:800].replace(chr(10), '<br>')}{'<br><i>…(truncated for display)</i>' if len(user) > 800 else ''}
    </div>
    """, unsafe_allow_html=True)


def notice_box(text: str):
    st.markdown(f'<div class="notice-box">💡 <b>What to notice:</b> {text}</div>',
                unsafe_allow_html=True)


def backend_pill():
    if get_backend() == "Ollama":
        st.markdown(f'<span class="ollama-pill">🖥️ Ollama · {get_ollama_model()}</span>',
                    unsafe_allow_html=True)
    elif get_backend() == "Gemini":
        st.markdown(f'<span class="gemini-pill">✨ Gemini · {get_gemini_model()}</span>',
                    unsafe_allow_html=True)
    else:
        model_short = "Haiku" if "haiku" in get_claude_model() else "Sonnet"
        st.markdown(f'<span class="claude-pill">☁️ Claude {model_short}</span>',
                    unsafe_allow_html=True)


def run_btn(label: str = "🚀 Run", key: str = "run") -> bool:
    if get_backend() == "Claude" and not get_api_key():
        st.warning("⚠️ Enter your Claude API key in the sidebar first.")
        return False
    if get_backend() == "Gemini" and not get_gemini_key():
        st.warning("⚠️ Enter your Google AI Studio key in the sidebar first. Get one free at aistudio.google.com")
        return False
    return st.button(label, key=key, type="primary")


def do_call(system: str, messages: list, max_tokens: int = 1200) -> tuple:
    t0 = time.perf_counter()
    backend = get_backend()
    if backend == "Ollama":
        label = f"Asking {get_ollama_model()} via Ollama…"
    elif backend == "Gemini":
        label = f"Calling Gemini ({get_gemini_model()})…"
    else:
        label = "Calling Claude…"

    with st.spinner(label):
        if backend == "Ollama":
            text, usage = call_ollama(system, messages,
                                      model=get_ollama_model(), max_tokens=max_tokens)
        elif backend == "Gemini":
            text, usage = call_gemini(get_gemini_key(), system, messages,
                                      model=get_gemini_model(), max_tokens=max_tokens)
        else:
            text, usage = call_claude(get_api_key(), system, messages,
                                      model=get_claude_model(), max_tokens=max_tokens)
    elapsed = time.perf_counter() - t0

    if text is None:
        if backend == "Ollama":
            st.error("❌ Could not reach Ollama. Is it running? Open a terminal and run: `ollama serve`")
        elif backend == "Gemini":
            st.error("❌ Gemini API call failed — check your key at aistudio.google.com → API Keys")
        else:
            st.error("❌ Claude API call failed — check your API key at console.anthropic.com")
    return text, usage, elapsed


def show_usage(usage, elapsed: float = None):
    cols = st.columns(3)
    if usage:
        cols[0].metric("Input tokens", f"{usage.input_tokens:,}")
        cols[1].metric("Output tokens", f"{usage.output_tokens:,}")
    if elapsed:
        cols[2].metric("Response time", f"{elapsed:.1f}s")


# ── Sidebar ────────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.title("🧪 Prompt Lab")
        st.caption("DevPro Academy · Prompt Engineering for Data Engineers")
        st.divider()

        st.subheader("⚡ Your Setup")
        backend_choice = st.radio(
            "I am using:",
            ["✨  Gemini  (Students — free)", "🖥️  Ollama Local  (Students)", "☁️  Claude API  (Trainer)"],
            index=0,
            help="Students use Gemini (free Google AI Studio key) or Ollama. Trainer uses Claude API.",
        )
        if "Gemini" in backend_choice:
            st.session_state.backend = "Gemini"
        elif "Ollama" in backend_choice:
            st.session_state.backend = "Ollama"
        else:
            st.session_state.backend = "Claude"

        st.divider()

        if get_backend() == "Gemini":
            st.info("✨ Free for students — get your key at **aistudio.google.com → Get API Key**")
            gkey = st.text_input(
                "🔑 Google AI Studio Key",
                type="password",
                value=st.session_state.get("gemini_key", ""),
                placeholder="AIza...",
            )
            if gkey:
                st.session_state.gemini_key = gkey

            if st.button("Test Connection", key="test_gemini"):
                with st.spinner("Testing…"):
                    t, _ = call_gemini(gkey, "Reply with the single word OK.",
                                       [{"role": "user", "content": "ping"}],
                                       max_tokens=10)
                st.session_state.conn_status = "ok" if t else "error"

            status = st.session_state.get("conn_status")
            if status == "ok":
                st.success("✓ Connected to Gemini")
            elif status == "error":
                st.error("✗ Invalid key — check aistudio.google.com")

            st.session_state.gemini_model = st.radio(
                "Model:",
                ["gemini-3-flash-preview", "gemini-2.5-flash"],
                captions=["Latest · free tier", "Stable · free tier"],
                index=0,
            )

        elif get_backend() == "Ollama":
            st.success("✅ No API key needed!")
            st.caption("Ollama runs on your laptop. Make sure it's started.")
            st.code("ollama serve", language="bash")
            st.session_state.ollama_model = st.radio(
                "Model:",
                ["qwen2.5:7b", "qwen2.5:14b"],
                captions=["8 GB RAM", "16 GB RAM"],
                index=0,
            )
        else:
            # Pre-fill from Streamlit secrets if available (deployed mode)
            _default_key = st.secrets.get("ANTHROPIC_API_KEY", st.session_state.get("api_key", ""))
            if _default_key and not st.session_state.get("api_key"):
                st.session_state.api_key = _default_key
            key = st.text_input(
                "🔑 Anthropic API Key",
                type="password",
                value=st.session_state.get("api_key", ""),
                placeholder="sk-ant-...",
            )
            if key:
                st.session_state.api_key = key

            if st.button("Test Connection", key="test_conn"):
                with st.spinner("Testing…"):
                    text, err = call_claude(key, "Reply with the single word OK.",
                                            [{"role": "user", "content": "ping"}],
                                            max_tokens=10)
                if text:
                    st.session_state.conn_status = "ok"
                    st.session_state.conn_error = ""
                else:
                    st.session_state.conn_status = "error"
                    st.session_state.conn_error = str(err)

            status = st.session_state.get("conn_status")
            if status == "ok":
                st.success("✓ Connected to Claude")
            elif status == "error":
                st.error(f"✗ Error: {st.session_state.get('conn_error', 'unknown')}")

            st.session_state.claude_model = st.radio(
                "Model:",
                ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"],
                captions=["Fast & cheap", "Higher quality"],
                index=0,
            )

        st.divider()
        st.subheader("📚 Modules")
        module = st.radio(
            "Go to:",
            [
                "🏠  Introduction",
                "1️⃣  Shot-Based Prompting",
                "🧠  Chain-of-Thought",
                "👤  Role Prompting",
                "🔄  NL ↔ SQL",
                "📋  Structured Output",
                "🗃️  Context Engineering",
                "🔧  LangChain vs SDK",
                "📖  Prompt Library",
            ],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("DevPro Academy")
        return module


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 0 — INTRODUCTION
# ══════════════════════════════════════════════════════════════════════════════
def page_home():
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <h1 style="margin:0; font-size:28px;">🧪 Prompt Engineering for Data Engineers</h1>
        <div style="background:linear-gradient(135deg,#1a2f5e,#2563eb); color:white; padding:8px 18px;
                    border-radius:20px; text-align:center; white-space:nowrap;">
            <div style="font-size:11px; letter-spacing:1.5px; text-transform:uppercase; opacity:0.85;">Presented by</div>
            <div style="font-size:15px; font-weight:800; letter-spacing:0.5px;">DevPro Academy</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("""
        ### 🎯 What This Lab Teaches

        Prompt engineering is the skill of getting **exactly what you want** from an AI model.
        The same model. The same API call. Just a better-written prompt.

        Data Engineers who master this write SQL faster, debug pipelines quicker,
        and generate documentation in seconds — all without leaving their editor.

        A great prompt is like a great job brief: the clearer you are,
        the better the result. By the end of this lab, you will have built your own
        **personal prompt library** for real Data Engineering tasks.

        ---

        ### 🗺️ How This Lab Works

        Each module is a **mini-experiment**:

        1. Read the plain-English explanation (30 seconds)
        2. Look at the exact prompt being sent to the AI — **this is the key learning**
        3. Click **Run** and watch the response
        4. Tweak one thing and run again — see what changes

        > 💡 **The golden rule:** You learn prompting by *doing*, not by reading.
        > Click Run early and often.
        """)

        st.divider()
        st.markdown("**Colour guide used throughout:**")
        c1, c2 = st.columns(2)
        c1.markdown('<span class="tag-system">🟢 ROLE (System)</span> — who the AI is pretending to be',
                    unsafe_allow_html=True)
        c2.markdown('<span class="tag-user">🔵 QUESTION (User)</span> — what you actually ask',
                    unsafe_allow_html=True)

    with col2:
        st.markdown("### 📋 8 Modules")
        modules = [
            ("1️⃣", "Shot-Based Prompting",  "Give examples → get better answers"),
            ("🧠", "Chain-of-Thought",       "Make AI think before answering"),
            ("👤", "Role Prompting",          "Pick your expert, get expert answers"),
            ("🔄", "NL ↔ SQL",               "English → SQL and SQL → English"),
            ("📋", "Structured Output",       "Force AI to return clean JSON/YAML"),
            ("🗃️", "Context Engineering",     "Manage token budgets smartly"),
            ("🔧", "LangChain vs SDK",        "Two ways to call AI — compare them"),
            ("📖", "Prompt Library",          "Build & export your personal toolkit"),
        ]
        for icon, title, desc in modules:
            st.markdown(f"**{icon} {title}**  \n*{desc}*")
            st.markdown("")

        st.divider()
        st.info("🏆 **Deliverable:** Export your `de_prompt_library.md` from Module 8 — your personal AI toolkit.")


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — SHOT-BASED PROMPTING
# ══════════════════════════════════════════════════════════════════════════════
def page_shot_prompting():
    mission_banner(
        "1️⃣", "Shot-Based Prompting",
        "Ask the same question 3 ways — watch the quality jump with each example you add.",
        "giving AI examples is like briefing a new team member — more context = better output"
    )

    backend_pill()

    show_steps([
        ("Type your business question", "The DE Task box below is the question you want answered. You can edit it to anything you like."),
        ("Choose a strategy", "Zero-shot = no examples (just ask). One-shot = show 1 example first. Few-shot = show 2-3 examples. Same question — different packaging."),
        ("See the prompt", "The green/blue boxes show exactly what gets sent to the AI. Notice how the USER section grows as you add examples."),
        ("Click Run & compare", "Run all 3 strategies on the same question. The output quality should improve each time."),
    ])

    st.divider()

    tab0, tab1, tab2, tab3 = st.tabs(
        ["📖 Zero-shot explained", "📖 One-shot explained", "📖 Few-shot explained", "🔬 Live Experiment"]
    )

    with tab0:
        st.markdown("### Zero-shot — Just Ask")
        st.markdown("""
        You send the question with **no examples**. The AI uses only its training knowledge.

        Think of it like emailing a question to a stranger — they'll answer based on what
        they generally know, not your specific style or standards.
        """)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="prompt-box prompt-system"><div class="prompt-label sys-label">🟢 ROLE (System)</div>You are a SQL expert.</div>', unsafe_allow_html=True)
            st.markdown('<div class="prompt-box prompt-user"><div class="prompt-label usr-label">🔵 QUESTION (User)</div>Write SQL to find the top 5 customers by revenue.</div>', unsafe_allow_html=True)
        with col2:
            st.success("✅ **Use when:** Quick exploration, one-off queries, format doesn't matter much.")
            st.warning("⚠️ **Problem:** Output style is unpredictable — different runs may look completely different.")

    with tab1:
        st.markdown("### One-shot — Show One Example First")
        st.markdown("""
        Before asking your question, you show the AI **one example** of the exact output style you want.
        It copies that style for your actual question.

        Like giving a new employee one sample report and saying *"format it like this."*
        """)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="prompt-box prompt-system"><div class="prompt-label sys-label">🟢 ROLE (System)</div>You are a SQL expert who generates production-ready queries.</div>', unsafe_allow_html=True)
            st.markdown('<div class="prompt-box prompt-user"><div class="prompt-label usr-label">🔵 QUESTION (User)</div><b>EXAMPLE:</b><br>Q: Top 5 customers<br>SQL: SELECT customer_id, SUM(amount)...<br><br><b>Now write:</b> your actual question here</div>', unsafe_allow_html=True)
        with col2:
            st.success("✅ **Use when:** You need a specific column-naming style or comment format.")
            st.info("💡 The example doesn't have to be related to your real question — it just sets the style.")

    with tab2:
        st.markdown("### Few-shot — Show 2-3 Examples")
        st.markdown("""
        You provide **2-3 examples** before asking your real question. The AI picks up your
        exact team standards — column aliases, comment format, CTE style, everything.

        This is the most powerful approach for production SQL that needs to match
        your company's coding standards.
        """)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="prompt-box prompt-system"><div class="prompt-label sys-label">🟢 ROLE (System)</div>You are a SQL expert. Match our coding standards exactly.</div>', unsafe_allow_html=True)
            st.markdown('<div class="prompt-box prompt-user"><div class="prompt-label usr-label">🔵 QUESTION (User)</div><b>EXAMPLE 1:</b> Daily revenue...<br><b>EXAMPLE 2:</b> Active customers...<br><br><b>Now write:</b> your actual question</div>', unsafe_allow_html=True)
        with col2:
            st.success("✅ **Use when:** Production SQL that must match your team's exact style guide.")
            st.warning("⚠️ More examples = more tokens = slightly more cost. Worth it for consistency.")

    with tab3:
        st.markdown("### 🔬 Run the Experiment")
        st.markdown("Type a business question → pick a strategy → click Run → see the difference in output quality.")

        task = st.text_area(
            "📝 Your business question (the DE Task):",
            value="Find customers who placed more than 3 orders in the last 90 days — show their email and total spend",
            height=80,
        )
        shot_type = st.radio(
            "Strategy — how many examples should we give the AI?",
            ["Zero-shot", "One-shot", "Few-shot"],
            horizontal=True,
            help="Try all 3 on the same question and compare the outputs.",
        )

        system, user = build_shot_prompt(task, shot_type)
        show_prompt(system, user)

        st.markdown(f"""
        **What changes between the 3 strategies?**
        Your question (*DE Task*) stays exactly the same.
        Only the number of examples before it changes.
        """)

        if run_btn("🚀 Run — See the Output", key="shot_run"):
            text, usage, elapsed = do_call(system, [{"role": "user", "content": user}])
            if text:
                st.markdown(f"#### 📤 Output — {shot_type}")
                st.markdown(text)
                show_usage(usage, elapsed)
                notice_box(
                    f"You used <b>{shot_type}</b>. "
                    "Now change the strategy to a different option and click Run again. "
                    "Does the SQL structure or comment style change? That's the lesson."
                )


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — CHAIN-OF-THOUGHT
# ══════════════════════════════════════════════════════════════════════════════
DE_SCENARIOS = [
    "Airflow DAG failing intermittently — no error message visible in logs",
    "Snowflake query suddenly taking 10x longer than last week",
    "Glue crawler stopped detecting new S3 partitions after adding a new folder",
    "dbt model failing with: 'relation does not exist'",
    "Kinesis consumer falling behind — shards at 100% utilisation",
]


def page_cot_react():
    mission_banner(
        "🧠", "Chain-of-Thought Prompting",
        "Make the AI think step-by-step before answering — like a doctor examining you properly instead of guessing.",
        "structured reasoning gives dramatically better answers for complex problems"
    )

    backend_pill()

    show_steps([
        ("Understand the problem", "Without CoT, the AI jumps straight to an answer — like a doctor guessing your diagnosis in 2 seconds. Fast but often wrong."),
        ("Enable step-by-step thinking", "With CoT, you tell the AI: 'Reason through this before answering.' It slows down, examines the problem, and gives a much better answer."),
        ("See the difference", "Use the toggle below to switch CoT on and off on the SAME problem. Compare the two responses side by side."),
        ("Try the ReAct tab", "ReAct takes it further — Thought → Action → Observation loops, exactly how a senior engineer would debug a production incident."),
    ])

    st.divider()

    tab_cot, tab_react = st.tabs(["🧠 Chain-of-Thought", "🔁 ReAct Debugging"])

    with tab_cot:
        st.markdown("### Without CoT vs With CoT — Same Problem, Different Depth")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### ❌ Without CoT")
            st.markdown("The AI jumps straight to a generic answer. Like asking for directions and getting: *'Go north.'*")
            st.markdown('<div class="prompt-box prompt-user"><div class="prompt-label usr-label">🔵 QUESTION</div>My Glue job fails with OOM on a 50 GB CSV. What should I do?</div>', unsafe_allow_html=True)
            st.caption("Result: generic tips. Increase memory, use partitioning... you've seen these before.")
        with col2:
            st.markdown("#### ✅ With CoT")
            st.markdown("The AI examines the problem first, then answers. Like a consultant who asks questions before recommending.")
            st.markdown('<div class="prompt-box prompt-user"><div class="prompt-label usr-label">🔵 QUESTION</div>My Glue job fails with OOM on a 50 GB CSV.<br><br><b>Think step by step:</b><br>1. What causes OOM in Glue?<br>2. What is specific about 50 GB CSV?<br>3. Solutions ranked by impact?<br>4. Exact config changes?</div>', unsafe_allow_html=True)
            st.caption("Result: structured, ordered, specific — with exact config values.")

        st.divider()

        problem = st.text_area(
            "📝 Paste your DE problem here:",
            value="My PySpark job runs 4x slower after upgrading from Databricks Runtime 12 to 14. Memory usage looks the same. What is going on and how do I fix it?",
            height=90,
        )
        use_cot = st.toggle("🧠 Enable step-by-step thinking (CoT)", value=True)

        system, user = build_cot_prompt(problem, use_cot)
        show_prompt(system, user)

        if use_cot:
            st.info("CoT is ON — notice how the USER section ends with 'Reason through this step by step'. That's the magic instruction.")
        else:
            st.warning("CoT is OFF — the question is sent raw. Turn it ON and compare the output.")

        if run_btn("🚀 Run", key="cot_run"):
            text, usage, elapsed = do_call(system, [{"role": "user", "content": user}], max_tokens=1500)
            if text:
                st.markdown(f"#### 📤 Output — {'With CoT ✅' if use_cot else 'Without CoT ❌'}")
                st.markdown(text)
                show_usage(usage, elapsed)
                if use_cot:
                    notice_box("See how the answer has numbered sections and works through the problem logically? Now toggle CoT OFF and run again. The difference is stark.")
                else:
                    notice_box("This is the raw answer with no guidance. Now toggle CoT ON and run again. The structured version is almost always more useful.")

    with tab_react:
        st.markdown("### ReAct — How a Senior Engineer Debugs Production Issues")
        st.markdown("""
        ReAct is a prompting pattern that mimics how a real engineer investigates a problem.
        Instead of guessing, it cycles through:

        > **THOUGHT** → What do I know? What do I need to figure out?
        > **ACTION** → What would I actually check or run right now?
        > **OBSERVATION** → What would I likely find?
        > *(repeat 3-5 times)*
        > **FINAL ANSWER** → Root cause + fix steps

        This is extremely useful for creating AI-powered runbooks and incident response guides.
        """)

        scenario = st.selectbox(
            "🚨 Pick a real production scenario to debug:",
            DE_SCENARIOS,
        )

        system, user = build_react_prompt(scenario)
        show_prompt(system, user)

        if run_btn("🔬 Debug This Incident", key="react_run"):
            text, usage, elapsed = do_call(system, [{"role": "user", "content": user}], max_tokens=1600)
            if text:
                st.markdown("#### 📤 ReAct Debug Trace")
                st.markdown(text)
                show_usage(usage, elapsed)
                notice_box(
                    "Count how many Thought → Action → Observation cycles the AI went through. "
                    "Each cycle narrows the problem. The Final Answer is usually very specific — "
                    "this is how you'd write an AI-powered incident runbook."
                )


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 3 — ROLE PROMPTING
# ══════════════════════════════════════════════════════════════════════════════
def page_role_prompting():
    mission_banner(
        "👤", "Role Prompting",
        "Same question — completely different answer depending on who you ask. Pick your expert.",
        "the System prompt defines WHO the AI is — changing it changes everything"
    )

    backend_pill()

    show_steps([
        ("Understand what 'role' means", "The green ROLE box tells the AI to pretend it's a specific type of expert — a cost-obsessed architect, a quality engineer, a sceptical tech lead. Each expert has different priorities."),
        ("Ask one question to one role", "Type your question, pick a role, and run. Read the answer."),
        ("Ask the SAME question to a different role", "Change only the role. Don't change the question. Run again. The advice will be completely different — sometimes even contradictory."),
        ("Try the side-by-side comparison", "The bottom section runs two roles simultaneously so you can compare their answers on one screen."),
    ])

    st.divider()

    st.markdown("### Ask One Expert")

    col1, col2 = st.columns([1, 1])
    with col1:
        role = st.selectbox("👤 Pick your expert:", list(ROLES.keys()))
        question = st.text_area(
            "❓ Your question (try this on multiple roles):",
            value="Should we use Lambda architecture or Kappa architecture for our real-time analytics pipeline?",
            height=90,
        )
    with col2:
        st.markdown("#### What this expert believes:")
        st.info(f"**{role}**\n\n{ROLES[role]}")

    system, user = build_role_prompt(role, question)
    show_prompt(system, user)

    if run_btn("🚀 Ask This Expert", key="role_single"):
        text, usage, elapsed = do_call(system, [{"role": "user", "content": user}])
        if text:
            st.markdown(f"#### 📤 Answer from: *{role}*")
            st.markdown(text)
            show_usage(usage, elapsed)
            notice_box(
                "Now go back and change the expert — keep the exact same question. "
                "A cost-focused architect and a quality engineer will give very different advice. "
                "Neither is wrong — they have different priorities."
            )

    st.divider()

    st.markdown("### 🔬 Side-by-Side — Two Experts, One Question")
    st.markdown("Run the same question through two different experts simultaneously and compare their thinking.")

    compare_q = st.text_input(
        "❓ Question for both experts:",
        value="Is it worth migrating from Airflow to Prefect for our data pipelines?",
    )

    role_names = list(ROLES.keys())
    col_a, col_b = st.columns(2)
    with col_a:
        role_a = st.selectbox("Expert A:", role_names, index=0, key="ra")
    with col_b:
        role_b = st.selectbox("Expert B:", role_names, index=3, key="rb")

    if run_btn("🔬 Ask Both Experts", key="role_compare"):
        sys_a, usr_a = build_role_prompt(role_a, compare_q)
        sys_b, usr_b = build_role_prompt(role_b, compare_q)

        with st.spinner("Getting both perspectives…"):
            if get_backend() == "Claude":
                res_a, _ = call_claude(get_api_key(), sys_a, [{"role": "user", "content": usr_a}],
                                       model=get_claude_model(), max_tokens=600)
                res_b, _ = call_claude(get_api_key(), sys_b, [{"role": "user", "content": usr_b}],
                                       model=get_claude_model(), max_tokens=600)
            elif get_backend() == "Gemini":
                res_a, _ = call_gemini(get_gemini_key(), sys_a, [{"role": "user", "content": usr_a}],
                                       model=get_gemini_model(), max_tokens=600)
                res_b, _ = call_gemini(get_gemini_key(), sys_b, [{"role": "user", "content": usr_b}],
                                       model=get_gemini_model(), max_tokens=600)
            else:
                res_a, _ = call_ollama(sys_a, [{"role": "user", "content": usr_a}],
                                       model=get_ollama_model(), max_tokens=600)
                res_b, _ = call_ollama(sys_b, [{"role": "user", "content": usr_b}],
                                       model=get_ollama_model(), max_tokens=600)

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown(f"**{role_a}**")
            if res_a:
                st.markdown(res_a)
            else:
                st.error("No response")
        with col_r2:
            st.markdown(f"**{role_b}**")
            if res_b:
                st.markdown(res_b)
            else:
                st.error("No response")

        if res_a and res_b:
            notice_box(
                "Same question — but look at the differences in priorities, tone, and recommendations. "
                "This is why the System prompt is so powerful: it controls the entire frame of the answer."
            )


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 4 — NL ↔ SQL
# ══════════════════════════════════════════════════════════════════════════════
EXAMPLE_SQL = """WITH customer_spend AS (
    SELECT
        c.customer_id,
        c.name,
        c.tier,
        COUNT(DISTINCT o.order_id)                             AS total_orders,
        SUM(o.amount)                                          AS lifetime_value,
        MAX(o.created_at)                                      AS last_order_date,
        AVG(o.amount)                                          AS avg_order_value,
        DATEDIFF('day', MIN(o.created_at), MAX(o.created_at)) AS tenure_days
    FROM sigma.customers c
    JOIN sigma.orders o ON c.customer_id = o.customer_id
    WHERE o.status = 'delivered'
    GROUP BY 1, 2, 3
),
ranked AS (
    SELECT *,
        PERCENT_RANK() OVER (PARTITION BY tier ORDER BY lifetime_value DESC) AS value_pct_rank
    FROM customer_spend
    WHERE total_orders >= 3
)
SELECT * FROM ranked WHERE value_pct_rank <= 0.10;"""

AUDIENCES = [
    "Business Analyst (no SQL knowledge)",
    "Junior Developer (knows basic SQL)",
    "Product Manager (needs the business so-what)",
    "Data Architect (full technical + performance detail)",
]


def page_nl_sql():
    mission_banner(
        "🔄", "NL ↔ SQL — English ↔ SQL Translation",
        "Type a business question in plain English → get SQL. Or paste complex SQL → get a plain English explanation.",
        "schema grounding is the secret to accurate SQL generation"
    )

    backend_pill()

    tab_nl, tab_sql = st.tabs(["🔤 English → SQL", "🔁 SQL → Plain English"])

    with tab_nl:
        show_steps([
            ("Give the AI your table structure", "The Schema box tells the AI what tables and columns exist. Without this, the AI invents table names — and gets it wrong. This is called 'grounding'."),
            ("Type your business question in plain English", "No SQL needed. Just say what you want in natural language, like you'd ask a colleague."),
            ("Pick your SQL dialect", "Snowflake, PostgreSQL, BigQuery — same question, slightly different SQL syntax. The AI handles the difference."),
            ("Run and copy the SQL", "The generated SQL should be copy-paste ready for your query editor."),
        ])
        st.divider()

        col1, col2 = st.columns([3, 2])
        with col1:
            schema = st.text_area("📋 Schema (paste your table definitions here):", DEFAULT_SCHEMA, height=200)
            nl_q = st.text_area(
                "💬 Business question in plain English:",
                value="Show me the top 10 gold and platinum customers by total spending in the last 6 months — only those with at least 5 delivered orders",
                height=80,
            )
            dialect = st.selectbox("🗄️ SQL dialect:", ["Snowflake", "PostgreSQL", "BigQuery", "Spark SQL"])
        with col2:
            st.markdown("#### 🔑 Why the schema matters")
            st.markdown("""
            **Without schema** → AI invents table names like `customer_data`, `purchases` — wrong.

            **With schema** → AI knows the exact tables and columns — copy-paste ready SQL.

            Try this experiment:
            1. Run with the schema as-is
            2. Delete everything from the Schema box
            3. Run again

            Watch how the quality collapses when the AI has no grounding.
            """)

        system, user = build_nl_sql_prompt(schema, nl_q, dialect)
        show_prompt(system, user)

        if run_btn("⚡ Generate SQL", key="nl_sql_run"):
            text, usage, elapsed = do_call(system, [{"role": "user", "content": user}])
            if text:
                st.markdown("#### 📤 Generated SQL")
                st.markdown(text)
                show_usage(usage, elapsed)
                notice_box(
                    "Check the table names in the SQL — they should match your schema exactly. "
                    "Now delete the schema and run again to see what happens without grounding."
                )

    with tab_sql:
        show_steps([
            ("Paste a complex SQL query", "Take any SQL from your project — the more complex the better. CTEs, window functions, nested subqueries — all fine."),
            ("Pick who needs the explanation", "A business analyst and a data architect need completely different explanations of the same query."),
            ("Run and read the explanation", "Use this to auto-document your entire dbt repository, or explain legacy SQL to new team members."),
        ])
        st.divider()

        col1, col2 = st.columns([3, 2])
        with col1:
            sql_in = st.text_area("📄 Paste SQL to explain:", EXAMPLE_SQL, height=280)
            audience = st.selectbox("👥 Explain it to:", AUDIENCES)
        with col2:
            st.markdown("#### 💼 Real use cases")
            st.markdown("""
            - Auto-document all `.sql` files in your dbt repo overnight
            - Generate column descriptions for your data catalog
            - Onboard new team members to legacy pipelines
            - Create plain-English summaries for stakeholder dashboards

            **In production**, you'd loop this over hundreds of SQL files:
            ```python
            for sql_file in all_sql_files:
                explanation = ask_ai(sql_file, audience="Business Analyst")
                update_catalog(sql_file, explanation)
            ```
            One afternoon of prompting = months of documentation work done.
            """)

        system, user = build_sql_nl_prompt(sql_in, audience)
        show_prompt(system, user)

        if run_btn("📖 Explain This SQL", key="sql_nl_run"):
            text, usage, elapsed = do_call(system, [{"role": "user", "content": user}])
            if text:
                st.markdown(f"#### 📤 Explanation for: *{audience}*")
                st.markdown(text)
                show_usage(usage, elapsed)
                notice_box(
                    f"This explanation is tailored for <b>{audience}</b>. "
                    "Now change the audience and run again — the exact same SQL gets a completely different explanation. "
                    "That's audience-aware prompting."
                )


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 5 — STRUCTURED OUTPUT
# ══════════════════════════════════════════════════════════════════════════════
DEFAULT_JSON_SCHEMA = """{
  "table_name": "string",
  "description": "string",
  "business_purpose": "string",
  "columns": [
    {"name": "string", "type": "string", "description": "string", "nullable": true, "pii": false}
  ],
  "tags": ["string"],
  "refresh_frequency": "string",
  "owner_team": "string"
}"""

DEFAULT_TABLE_DESC = """Table: sigma.orders
Columns: order_id, customer_id, status, amount, created_at, delivered_at
Business context: Central fact table for all customer orders. Source: Stripe webhooks via Kinesis Firehose."""


def page_structured_output():
    mission_banner(
        "📋", "Structured Output — Making AI Return Clean JSON & YAML",
        "AI output is messy text by default. Learn to force it into perfect JSON so your pipelines can use it automatically.",
        "how to get machine-readable output — critical for production pipelines"
    )

    backend_pill()

    show_steps([
        ("Understand the problem", "If AI returns 'Here is the JSON: ... Plus some notes at the bottom' — your json.loads() will crash. Production pipelines need EXACT, parseable output."),
        ("The trick — be very specific in the prompt", "Say exactly: 'Return ONLY valid JSON. No markdown. No explanation. Nothing else.' Then show the schema so the AI knows the structure."),
        ("Check if it worked", "The app automatically tries to parse the output. Green = it worked. Red = the AI added something extra. Watch how often it fails with weaker models."),
        ("Learn the retry pattern", "In production, if parsing fails, you send the error back to the AI and ask it to fix itself. This is called self-correction."),
    ])

    st.divider()

    tab_json, tab_yaml, tab_code = st.tabs(["📦 JSON Output", "📄 YAML Output", "🔧 Production Pattern"])

    with tab_json:
        col1, col2 = st.columns(2)
        with col1:
            table_desc = st.text_area("📋 Describe the table:", DEFAULT_TABLE_DESC, height=140)
        with col2:
            json_schema_str = st.text_area("🗂️ JSON structure to enforce:", DEFAULT_JSON_SCHEMA, height=220)

        system, user = build_json_prompt(table_desc, json_schema_str)
        show_prompt(system, user)
        st.info("Notice the ROLE says 'Return ONLY valid JSON. No markdown fences, no explanation.' — this is the critical instruction.")

        if run_btn("⚡ Generate JSON", key="json_run"):
            text, usage, elapsed = do_call(system, [{"role": "user", "content": user}])
            if text:
                col_r, col_v = st.columns(2)
                with col_r:
                    st.markdown("#### Raw AI output")
                    st.code(text, language="text")
                with col_v:
                    st.markdown("#### Can Python parse it?")
                    parsed, is_valid, error = parse_json_response(text)
                    if is_valid:
                        st.success("✅ Valid JSON — `json.loads()` worked!")
                        st.json(parsed)
                    else:
                        st.error(f"❌ Parse failed: {error}")
                        st.warning("The AI added extra text. Try a stronger instruction or use the retry pattern (Production Pattern tab).")
                show_usage(usage, elapsed)
                notice_box(
                    "Did it parse successfully? If not, look at what the AI added that broke the JSON. "
                    "Smaller/weaker models fail this more often. That's why production systems always include a retry loop."
                )

    with tab_yaml:
        st.markdown("### Describe a Pipeline in English → Get Airflow YAML Config")
        pipe_desc = st.text_area(
            "📝 Describe your pipeline in plain English:",
            value="A daily Airflow DAG at 6 AM that reads new orders from S3 raw/orders/, "
                  "runs a Glue job to clean and deduplicate, then upserts into "
                  "Redshift Serverless sigma_dw.fact_orders. Slack alert on failure.",
            height=100,
        )

        system, user = build_yaml_prompt(pipe_desc)
        show_prompt(system, user)

        if run_btn("⚡ Generate YAML", key="yaml_run"):
            text, usage, elapsed = do_call(system, [{"role": "user", "content": user}])
            if text:
                st.markdown("#### 📤 Pipeline YAML Config")
                st.code(text, language="yaml")
                show_usage(usage, elapsed)
                notice_box(
                    "Try changing the schedule, adding a second task, or changing the destination in the description — then re-run. "
                    "The AI updates the YAML accordingly. This is how you'd prototype pipeline configs quickly."
                )

    with tab_code:
        st.markdown("### The Self-Correcting Retry Pattern (Production Ready)")
        st.markdown("""
        In production, JSON output fails ~10-20% of the time even with the best prompt.
        The solution: catch the error, tell the AI what went wrong, and ask it to fix itself.
        """)
        st.code("""
import json

def get_json_from_ai(prompt, schema, max_retries=3):
    for attempt in range(max_retries):
        response = ask_ai(prompt)          # your call_claude() or call_ollama()
        try:
            return json.loads(response)    # ✅ worked — return it
        except json.JSONDecodeError as error:
            if attempt == max_retries - 1:
                raise                      # give up after 3 tries
            # ❌ failed — tell AI what went wrong and try again
            prompt = prompt + f"\\n\\nYour previous response failed to parse: {error}\\nFix it and return ONLY valid JSON."

# Usage
result = get_json_from_ai("Document the sigma.orders table", schema)
""", language="python")
        st.success("This pattern reduces parse failures from ~15% to near 0%. Always use it in production.")


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 6 — CONTEXT ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════
def page_context_engineering():
    mission_banner(
        "🗃️", "Context Engineering",
        "Every word you send costs tokens. Learn to pack the right information and manage long conversations.",
        "how to work with large schemas without hitting limits or wasting money"
    )

    backend_pill()

    show_steps([
        ("Understand the context window", "Think of the context window as a whiteboard. Claude's whiteboard holds 200,000 tokens (about 150,000 words). Everything you send — your prompt, the schema, the conversation history — must fit on this whiteboard."),
        ("Count your tokens before sending", "Paste any text into the Token Counter to see how many tokens it uses. A 50-table schema can be 5,000 tokens — that's fine. But 500 tables? You need a strategy."),
        ("Use the budget planner", "Drag the sliders to plan how you'll use your token budget across system prompt, schema, history, and current question."),
        ("Learn the 5 compression strategies", "When you hit limits, the Strategies tab shows 5 real techniques used in production DE pipelines."),
    ])

    st.divider()

    tab_tok, tab_conv, tab_strat = st.tabs(["🔢 Token Counter", "💬 Conversation Memory", "🛠️ Strategies"])

    with tab_tok:
        st.markdown("### How Many Tokens Is My Content?")

        col1, col2 = st.columns([2, 1])
        with col1:
            text_in = st.text_area(
                "📋 Paste any text to count its tokens (schema, SQL, config, etc.):",
                DEFAULT_SCHEMA, height=200
            )
        with col2:
            char_count = len(text_in)
            est = estimate_tokens(text_in)
            st.metric("Characters", f"{char_count:,}")
            st.metric("Estimated tokens", f"~{est:,}")
            pct = est / 2000
            st.metric("% of 200K context", f"{pct:.2f}%")
            st.divider()
            st.markdown("""
            **Quick rules:**
            - 1 token ≈ 4 characters
            - 1 page of SQL ≈ 500 tokens
            - 50-table schema ≈ 5,000 tokens
            - Average response ≈ 300 tokens
            """)

        st.markdown("---")
        st.markdown("### 📊 Token Budget Planner")
        st.markdown("Drag the sliders to see how your planned prompt will use the 200K token budget.")

        cols = st.columns(4)
        sys_t  = cols[0].slider("System prompt",       100, 5000,   500, 100)
        sch_t  = cols[1].slider("Schema context",        0, 20000,  2000, 500)
        hist_t = cols[2].slider("Conversation history",  0, 50000,  5000, 1000)
        qry_t  = cols[3].slider("Current question",    100, 2000,   200, 100)

        total_t = sys_t + sch_t + hist_t + qry_t
        pct2 = total_t / 200_000 * 100

        m1, m2, m3 = st.columns(3)
        m1.metric("Total tokens used", f"{total_t:,}")
        m2.metric("Context used",      f"{pct2:.1f}%")
        m3.metric("Left for output",   f"{200_000 - total_t:,}")
        st.progress(min(pct2 / 100, 1.0))

        if pct2 > 80:
            st.error("⚠️ Context nearly full — compress schema or trim history before hitting limits.")
        elif pct2 > 50:
            st.warning("Context is moderate — keep an eye on it as conversation grows.")
        else:
            st.success("✅ Context budget is healthy.")

    with tab_conv:
        st.markdown("### How Conversation Memory Works")
        st.markdown("""
        Every time you send a message, the AI receives the **entire conversation history** —
        not just your latest message. This means costs grow with each turn.

        Try this: say *"I have a customers table with id, name, email"* then follow up with
        *"Write a dedup query for it"* — the AI remembers the table from your first message.
        """)

        if "ctx_msgs" not in st.session_state:
            st.session_state.ctx_msgs = []

        sys_ctx = "You are a SQL assistant for Sigma DataTech. Remember context from previous messages."
        user_msg = st.text_input(
            "💬 Your message:",
            placeholder="Try: 'I have a customers table with id, name, email' then follow up…",
        )

        col_send, col_clear = st.columns([1, 4])
        with col_send:
            send_disabled = (get_backend() == "Claude" and not get_api_key())
            if st.button("Send", key="ctx_send", disabled=send_disabled) and user_msg:
                st.session_state.ctx_msgs.append({"role": "user", "content": user_msg})
                with st.spinner("Thinking…"):
                    if get_backend() == "Ollama":
                        text, _ = call_ollama(sys_ctx, st.session_state.ctx_msgs, model=get_ollama_model())
                    elif get_backend() == "Gemini":
                        text, _ = call_gemini(get_gemini_key(), sys_ctx, st.session_state.ctx_msgs, model=get_gemini_model())
                    else:
                        text, _ = call_claude(get_api_key(), sys_ctx, st.session_state.ctx_msgs, model=get_claude_model())
                if text:
                    st.session_state.ctx_msgs.append({"role": "assistant", "content": text})
        with col_clear:
            if st.button("🗑️ Clear conversation", key="ctx_clear"):
                st.session_state.ctx_msgs = []

        for msg in st.session_state.ctx_msgs:
            icon = "👤" if msg["role"] == "user" else "🤖"
            preview = msg["content"][:300] + ("…" if len(msg["content"]) > 300 else "")
            st.markdown(f"**{icon}** {preview}")

        if st.session_state.ctx_msgs:
            approx = estimate_tokens("".join(m["content"] for m in st.session_state.ctx_msgs))
            st.progress(min(approx / 200_000, 1.0))
            st.caption(f"History so far: ~{approx:,} tokens ({approx / 2000:.2f}% of 200K context)")

    with tab_strat:
        st.markdown("### 5 Strategies When You Hit Context Limits")
        st.code("""
# Strategy 1: Compress your schema — DDL → compact notation (10x smaller)
# Before: 500 lines of CREATE TABLE statements
# After:  "customers(id,name,email,tier) | orders(id,cust_id,status,amount,dt)"

# Strategy 2: Sliding window — drop oldest messages when history grows
def trim_history(messages, max_tokens=40_000):
    while estimate_tokens("".join(m["content"] for m in messages)) > max_tokens:
        messages.pop(1)    # remove oldest message (keep system at index 0)
    return messages

# Strategy 3: Summarise old history then continue
def compress_history(messages):
    summary = ask_ai("Summarise this conversation in under 200 words", messages)
    return [{"role": "user", "content": f"Prior context: {summary}"}]

# Strategy 4: Only send relevant tables (find them by keyword search)
def focused_schema(question, all_tables):
    keywords = extract_keywords(question)
    relevant = [t for t in all_tables if any(k in t for k in keywords)]
    return build_ddl(relevant)   # send 5 tables instead of 500

# Strategy 5: Anthropic Prompt Caching — cache a large static schema
# First call is full price. Subsequent calls cost 90% less for the cached part.
response = client.messages.create(
    system=[{"type": "text", "text": your_large_schema,
             "cache_control": {"type": "ephemeral"}}],   # cached for 5 min
    messages=[{"role": "user", "content": dynamic_question}]
)
""", language="python")
        st.info("Strategy 1 (schema compression) is free and saves the most tokens. Always start there.")


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 7 — LANGCHAIN vs SDK (Claude API only)
# ══════════════════════════════════════════════════════════════════════════════
def page_langchain_vs_sdk():
    mission_banner(
        "🔧", "LangChain PromptTemplate — Build Reusable AI Workflows",
        "Learn what LangChain is, build your first chain using PromptTemplate, and run it live on your local Qwen model.",
        "how to build composable, reusable AI pipelines using LangChain PromptTemplate"
    )

    backend_pill()

    # ── What is LangChain — detailed explanation ───────────────────────────────
    st.markdown("### 🤔 What is LangChain?")
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("""
        **LangChain** is a Python framework for building applications that use AI models.

        Without LangChain, calling an AI looks like this:
        ```python
        # You manually build the prompt string
        prompt = f"You are a SQL expert. Write SQL for: {question}"
        # You manually call the API
        response = requests.post("http://localhost:11434/api/chat", json={...})
        # You manually extract the text
        result = response.json()["message"]["content"]
        ```

        With LangChain, the same thing looks like this:
        ```python
        chain = template | ChatOllama(model="qwen2.5:7b") | StrOutputParser()
        result = chain.invoke({"question": "Find top customers"})
        ```

        Same result. But the LangChain version is:
        - **Reusable** — use the same template for 1,000 different tables
        - **Swappable** — change `ChatOllama` to `ChatAnthropic` in one line to switch models
        - **Chainable** — connect multiple AI steps together like assembly line workers
        """)
    with col2:
        st.markdown("### 🧱 The 3 Building Blocks")
        st.info("""
**1. PromptTemplate**
Manages your prompt with `{variable}` placeholders.
Like a Word document with fill-in-the-blank fields.
Variables get filled at runtime — different values each call.

---

**2. ChatOllama / ChatAnthropic**
The AI model connector.
Takes the filled prompt → sends to the AI → gets response back.
Swap this one line to change your AI provider.

---

**3. StrOutputParser**
Converts the AI's response object into a plain Python string.
Without it, you get a complex AIMessage object.
With it, you get clean text you can use directly.
        """)

    st.divider()
    st.markdown("### ⛓️ How a Chain Works — Step by Step")
    st.markdown("""
    The `|` (pipe) operator connects blocks. Output of one becomes input of the next:
    """)
    st.code("""
# Step 1 — Define the template with {placeholders}
from langchain_core.prompts import PromptTemplate

template = PromptTemplate(
    input_variables=["dialect", "table", "question"],
    template=\"\"\"You are a {dialect} SQL expert at Sigma DataTech.
Table: {table}
Write SQL to: {question}
Return ONLY the SQL in a code block.\"\"\"
)

# Step 2 — Connect template → model → parser using the | pipe operator
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser

chain = template | ChatOllama(model="qwen2.5:7b") | StrOutputParser()
#        ↑                    ↑                      ↑
#   fills variables      sends to Qwen          gives clean text

# Step 3 — Invoke the chain with your values
result = chain.invoke({
    "dialect":  "Snowflake",
    "table":    "sigma.orders",
    "question": "Find top 10 customers by revenue last 90 days"
})

print(result)   # → clean SQL string, ready to use
""", language="python")

    st.divider()

    show_steps([
        ("Template Builder tab", "Write a prompt template with {variables}. Fill in the values. See the filled prompt. Run it with LangChain — watch the chain execute live."),
        ("Direct vs LangChain tab", "Same prompt, two paths. Direct call (requests) vs LangChain chain. Output is identical — see what LangChain adds in code simplicity and flexibility."),
        ("When to use which tab", "Decision guide — when LangChain is overkill vs when it pays off."),
    ])

    st.divider()

    tab_builder, tab_compare, tab_why = st.tabs(
        ["🧩 PromptTemplate Builder", "⚡ Direct vs LangChain Live", "📊 When to Use Which?"]
    )

    # ── Tab 1: PromptTemplate Builder ─────────────────────────────────────────
    with tab_builder:
        st.markdown("### Build and Run a LangChain PromptTemplate")
        st.markdown("""
        Write a template below. Use `{variable_name}` for any part that should change
        between calls. Fill in the values on the right. Then run it using a real
        LangChain chain — `PromptTemplate | ChatOllama | StrOutputParser`.
        """)

        col1, col2 = st.columns(2)
        with col1:
            template_text = st.text_area(
                "📝 Your prompt template (use {variable} placeholders):",
                value="""You are a {role} at Sigma DataTech.

Table: {table_name}
Schema: {schema}

Task: {task}

Format your response as {output_format}.""",
                height=240,
            )
            detected_vars = list(dict.fromkeys(re.findall(r'\{(\w+)\}', template_text)))
            if detected_vars:
                st.success(f"✅ Variables detected: `{'`, `'.join(detected_vars)}`")
                st.caption("Each variable must be filled in on the right before running.")

        with col2:
            st.markdown("#### Fill the Variables")
            st.caption("These replace the {placeholders} in your template at runtime.")
            var_defaults = {
                "role":          "Senior Data Engineer",
                "table_name":    "sigma.orders",
                "schema":        "order_id BIGINT, customer_id BIGINT, status VARCHAR, amount DECIMAL",
                "task":          "Write data quality rules to validate this table",
                "output_format": "a numbered list with severity (critical/warning/info) for each rule",
            }
            var_values = {}
            for var in detected_vars:
                var_values[var] = st.text_input(
                    f"`{{{var}}}`",
                    value=var_defaults.get(var, ""),
                    key=f"tv_{var}",
                )

        filled = fill_template(template_text, var_values)

        st.markdown("#### 📨 Filled Prompt — what LangChain will send to the AI")
        st.code(filled, language="text")

        st.markdown("#### Equivalent Python code that runs when you click Run:")
        if get_backend() == "Ollama":
            model_name   = get_ollama_model()
            model_import = "from langchain_community.chat_models import ChatOllama"
            model_init   = f'ChatOllama(model="{model_name}")'
        elif get_backend() == "Gemini":
            model_name   = get_gemini_model()
            model_import = "from langchain_google_genai import ChatGoogleGenerativeAI"
            model_init   = f'ChatGoogleGenerativeAI(model="{model_name}")'
        else:
            model_name   = get_claude_model()
            model_import = "from langchain_anthropic import ChatAnthropic"
            model_init   = f'ChatAnthropic(model_name="{model_name}")'
        st.code(f"""
{model_import}
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

template = PromptTemplate(
    input_variables={detected_vars},
    template=YOUR_TEMPLATE_STRING,
)

chain = template | {model_init} | StrOutputParser()
#        ↑              ↑                  ↑
#  fills variables   sends to AI     clean text out

result = chain.invoke({{{', '.join(f'"{v}": "..."' for v in detected_vars)}}})
""", language="python")

        if run_btn("🚀 Run with LangChain Chain", key="tpl_run"):
            try:
                if get_backend() == "Ollama":
                    from langchain_community.chat_models import ChatOllama
                    from langchain_core.prompts import ChatPromptTemplate as LCTemplate
                    from langchain_core.output_parsers import StrOutputParser
                    lc_prompt = LCTemplate.from_messages([
                        ("system", "You are a helpful data engineering assistant."),
                        ("human", "{filled_prompt}"),
                    ])
                    lc_model = ChatOllama(model=get_ollama_model())
                    lc_chain = lc_prompt | lc_model | StrOutputParser()
                    with st.spinner(f"LangChain → {get_ollama_model()} running…"):
                        t0 = time.perf_counter()
                        text = lc_chain.invoke({"filled_prompt": filled})
                        elapsed = time.perf_counter() - t0
                elif get_backend() == "Gemini":
                    # Gemini via direct call (langchain-google-genai not pre-installed)
                    st.info("💡 Gemini LangChain integration needs `pip install langchain-google-genai`. Running via direct Gemini API instead.")
                    with st.spinner(f"Gemini ({get_gemini_model()}) running…"):
                        t0 = time.perf_counter()
                        text, _ = call_gemini(get_gemini_key(),
                                              "You are a helpful data engineering assistant.",
                                              [{"role": "user", "content": filled}],
                                              model=get_gemini_model(), max_tokens=800)
                        elapsed = time.perf_counter() - t0
                else:
                    from langchain_core.prompts import ChatPromptTemplate as LCTemplate
                    from langchain_anthropic import ChatAnthropic
                    from langchain_core.output_parsers import StrOutputParser
                    lc_prompt = LCTemplate.from_messages([
                        ("system", "You are a helpful data engineering assistant."),
                        ("human", "{filled_prompt}"),
                    ])
                    lc_model = ChatAnthropic(api_key=get_api_key(), model_name=get_claude_model(), max_tokens=800)
                    lc_chain = lc_prompt | lc_model | StrOutputParser()
                    with st.spinner("LangChain → Claude running…"):
                        t0 = time.perf_counter()
                        text = lc_chain.invoke({"filled_prompt": filled})
                        elapsed = time.perf_counter() - t0

                st.markdown("#### 📤 Output from LangChain Chain")
                st.markdown(text)
                st.metric("Response time", f"{elapsed:.1f}s")
                notice_box(
                    "You just ran a real LangChain chain: "
                    "<b>PromptTemplate → ChatOllama → StrOutputParser</b>. "
                    "Now try changing a variable value and running again — "
                    "the same chain, different data. That's the power of templates."
                )
            except Exception as e:
                st.error(f"LangChain error: {e}")
                st.info("Make sure langchain-community is installed: `pip install langchain-community`")

    # ── Tab 2: Direct vs LangChain ────────────────────────────────────────────
    with tab_compare:
        st.markdown("### Same Prompt — Direct API Call vs LangChain Chain")
        st.markdown("""
        Both approaches call the same AI model with the same prompt.
        The output will be identical.
        The difference is in the **code** — and what each approach enables.
        """)

        sys_prompt = st.text_area(
            "System (Role):",
            value="You are a senior Data Engineer at Sigma DataTech. Be concise and practical.",
            height=60,
        )
        usr_prompt = st.text_area(
            "User (Question):",
            value="What are the 3 most important things to check when a dbt model fails in production?",
            height=70,
        )

        if run_btn("⚡ Run Both — Compare Side by Side", key="compare_run"):
            col_sdk, col_lc = st.columns(2)

            with col_sdk:
                st.markdown('<div class="sdk-header">🟠 Direct API Call (requests / SDK)</div>',
                            unsafe_allow_html=True)
                if get_backend() == "Ollama":
                    st.code("""import requests

response = requests.post(
    "http://localhost:11434/api/chat",
    json={
        "model": "qwen2.5:7b",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ],
        "stream": False
    }
)
result = response.json()["message"]["content"]""", language="python")
                else:
                    st.code("""client = Anthropic(api_key=key)
resp = client.messages.create(
    model=model,
    system=system,
    messages=[{"role":"user","content":user}]
)
result = resp.content[0].text""", language="python")

                with st.spinner("Direct call running…"):
                    t0 = time.perf_counter()
                    sdk_text, _ = do_call(sys_prompt,
                                          [{"role": "user", "content": usr_prompt}],
                                          max_tokens=500)[:2]
                    sdk_elapsed = time.perf_counter() - t0
                st.metric("Response time", f"{sdk_elapsed:.2f}s")
                if sdk_text:
                    st.markdown(sdk_text)

            with col_lc:
                st.markdown('<div class="lc-header">🟣 LangChain Chain</div>',
                            unsafe_allow_html=True)
                st.code("""from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human",  "{input}"),
])
chain = prompt | ChatOllama(model="qwen2.5:7b") | StrOutputParser()
result = chain.invoke({"input": user_prompt})""", language="python")

                lc_error = None
                try:
                    if get_backend() == "Ollama":
                        from langchain_community.chat_models import ChatOllama
                        from langchain_core.prompts import ChatPromptTemplate as LCTemplate
                        from langchain_core.output_parsers import StrOutputParser
                        lc_chain = (
                            LCTemplate.from_messages([("system", sys_prompt), ("human", "{input}")])
                            | ChatOllama(model=get_ollama_model())
                            | StrOutputParser()
                        )
                        with st.spinner("LangChain chain running…"):
                            t0 = time.perf_counter()
                            lc_text = lc_chain.invoke({"input": usr_prompt})
                            lc_elapsed = time.perf_counter() - t0
                    elif get_backend() == "Gemini":
                        st.info("💡 Gemini LangChain needs `pip install langchain-google-genai`. Running via direct API.")
                        with st.spinner(f"Gemini direct call running…"):
                            t0 = time.perf_counter()
                            lc_text, _ = call_gemini(get_gemini_key(), sys_prompt,
                                                     [{"role": "user", "content": usr_prompt}],
                                                     model=get_gemini_model(), max_tokens=500)
                            lc_elapsed = time.perf_counter() - t0
                    else:
                        from langchain_anthropic import ChatAnthropic
                        from langchain_core.prompts import ChatPromptTemplate as LCTemplate
                        from langchain_core.output_parsers import StrOutputParser
                        lc_chain = (
                            LCTemplate.from_messages([("system", sys_prompt), ("human", "{input}")])
                            | ChatAnthropic(api_key=get_api_key(), model_name=get_claude_model(), max_tokens=500)
                            | StrOutputParser()
                        )
                        with st.spinner("LangChain chain running…"):
                            t0 = time.perf_counter()
                            lc_text = lc_chain.invoke({"input": usr_prompt})
                            lc_elapsed = time.perf_counter() - t0
                except Exception as exc:
                    lc_text, lc_elapsed, lc_error = None, 0.0, str(exc)

                if lc_error:
                    st.error(f"LangChain error: {lc_error}")
                else:
                    st.metric("Response time", f"{lc_elapsed:.2f}s")
                    if lc_text:
                        st.markdown(lc_text)

            if sdk_text and lc_text and not lc_error:
                overhead = max(0.0, lc_elapsed - sdk_elapsed)
                notice_box(
                    f"<b>Same output.</b> LangChain added ~{overhead:.2f}s of setup overhead. "
                    "For a single call — direct is faster. "
                    "LangChain pays off when you need: "
                    "batch processing, streaming, model swapping, or observability. "
                    "See the next tab for when each approach wins."
                )

    # ── Tab 3: When to use which ───────────────────────────────────────────────
    with tab_why:
        st.markdown("### When Does LangChain Pay Off?")
        st.markdown("""
        | Situation | Direct API / SDK | LangChain Chain |
        |-----------|-----------------|-----------------|
        | One-off script, quick test | ✅ Simpler, fewer dependencies | Overkill |
        | Same prompt on 100 tables | Write a for-loop manually | `.batch([...])` — runs in parallel |
        | Stream output token by token | Write callbacks manually | `.stream(input)` — one line |
        | Swap from Qwen to Claude | Edit every file | Change one line: `ChatOllama → ChatAnthropic` |
        | Log every prompt + response | Add logging everywhere | `.with_listeners()` |
        | Connect multiple AI steps | Complex manual wiring | Chain with `|` naturally |
        """)

        st.markdown("#### Real example — batch document 50 tables in parallel:")
        st.code("""
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

template = PromptTemplate(
    input_variables=["table_name", "columns"],
    template="Document this table in 2 sentences. Table: {table_name}. Columns: {columns}"
)
chain = template | ChatOllama(model="qwen2.5:7b") | StrOutputParser()

# All 50 tables processed — LangChain handles concurrency
results = chain.batch([
    {"table_name": "sigma.orders",    "columns": "order_id, amount, status"},
    {"table_name": "sigma.customers", "columns": "customer_id, name, tier"},
    # ... 48 more tables
], config={"max_concurrency": 5})

# results = list of 50 documentation strings
# What took 30 minutes manually now takes 3 minutes
""", language="python")
        st.success("**Rule of thumb:** Start with direct calls. Add LangChain when you need to scale, swap models, or chain multiple AI steps together.")


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 8 — DE PROMPT LIBRARY
# ══════════════════════════════════════════════════════════════════════════════
def page_de_prompt_library():
    mission_banner(
        "📖", "Build Your Personal DE Prompt Library",
        "Test 6 real-world prompts, customise them to your style, and export your toolkit.",
        "by the end of this module, you will have a reusable prompt library you can use at work"
    )

    backend_pill()

    show_steps([
        ("Pick a prompt from the dropdown", "There are 6 real DE prompts — SQL generation, schema docs, error explanation, data quality rules, pipeline docs, and dbt stubs."),
        ("Read the template and edit it", "The template has {variable} placeholders. Customise the wording to match your team's style."),
        ("Fill in the variables and run it", "See the real output. If you don't like it, tweak the template and run again."),
        ("Export when all 6 are tested", "Click Generate → Download to get your personal de_prompt_library.md. This is your deliverable for today."),
    ])

    st.divider()

    if "lib_prompts" not in st.session_state:
        st.session_state.lib_prompts = copy.deepcopy(DE_PROMPTS)

    selected = st.selectbox("📌 Select a prompt to test and customise:", list(DE_PROMPTS.keys()))
    data = st.session_state.lib_prompts[selected]

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(f"### {data['icon']} {selected}")
        st.caption(f"**What this does:** {data['description']}")

        new_template = st.text_area(
            "📝 Template (edit the wording to match your style):",
            value=data["template"],
            height=260,
            key=f"tmpl_{selected}",
        )
        st.session_state.lib_prompts[selected]["template"] = new_template

        if st.button("↩ Reset to default", key=f"reset_{selected}"):
            st.session_state.lib_prompts[selected]["template"] = DE_PROMPTS[selected]["template"]
            st.session_state.lib_prompts[selected]["variables"] = copy.deepcopy(DE_PROMPTS[selected]["variables"])
            st.rerun()

    with col2:
        st.markdown("### Fill in the Variables")
        st.caption("Change these to match your actual tables and use case.")
        for var, default_val in DE_PROMPTS[selected]["variables"].items():
            new_val = st.text_area(
                f"`{{{var}}}`",
                value=st.session_state.lib_prompts[selected]["variables"].get(var, default_val),
                height=70,
                key=f"libvar_{selected}_{var}",
            )
            st.session_state.lib_prompts[selected]["variables"][var] = new_val

    filled = fill_template(
        st.session_state.lib_prompts[selected]["template"],
        st.session_state.lib_prompts[selected]["variables"],
    )
    show_prompt("You are an expert data engineering assistant at Sigma DataTech.", filled)

    col_run1, col_run2 = st.columns(2)

    with col_run1:
        if run_btn(f"🚀 Test This Prompt", key=f"lib_run_{selected}"):
            text, usage, elapsed = do_call(
                "You are an expert data engineering assistant at Sigma DataTech.",
                [{"role": "user", "content": filled}],
                max_tokens=1600,
            )
            if text:
                st.markdown("#### 📤 Output")
                st.markdown(text)
                show_usage(usage, elapsed)
                notice_box(
                    "Happy with the output? Move on to the next prompt in the dropdown. "
                    "Once you've tested all 6, export your library below."
                )

    with col_run2:
        st.markdown("**Or run it the production way:**")
        st.caption("LangChain PromptTemplate → Model → Parser")

    st.divider()

    # ── LangChain run for this prompt ──────────────────────────────────────────
    st.markdown("### 🔗 Run with LangChain PromptTemplate")
    st.markdown("""
    Your prompt template above uses `{variable}` placeholders — that's **exactly** the
    LangChain `PromptTemplate` syntax. Below is the production Python code for this prompt,
    and a button to run it live using a real LangChain chain.
    """)

    detected_lib_vars = list(dict.fromkeys(
        re.findall(r'\{(\w+)\}', st.session_state.lib_prompts[selected]["template"])
    ))
    if get_backend() == "Ollama":
        model_name_lib   = get_ollama_model()
        model_import_lib = "from langchain_community.chat_models import ChatOllama"
        model_init_lib   = f'ChatOllama(model="{model_name_lib}")'
    elif get_backend() == "Gemini":
        model_name_lib   = get_gemini_model()
        model_import_lib = "from langchain_google_genai import ChatGoogleGenerativeAI"
        model_init_lib   = f'ChatGoogleGenerativeAI(model="{model_name_lib}")'
    else:
        model_name_lib   = get_claude_model()
        model_import_lib = "from langchain_anthropic import ChatAnthropic"
        model_init_lib   = f'ChatAnthropic(model_name="{model_name_lib}")'
    current_vars = st.session_state.lib_prompts[selected]["variables"]
    invoke_lines = "\n".join(
        f'    "{v}": "{str(current_vars.get(v, "")).replace(chr(10), " ")[:50]}..."'
        for v in detected_lib_vars
    )

    st.code(f"""
{model_import_lib}
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

TEMPLATE = \"\"\"...your template from above...\"\"\"

template = PromptTemplate(
    input_variables={detected_lib_vars},
    template=TEMPLATE,
)

# | connects the blocks: template fills vars → model runs → parser returns clean text
chain = template | {model_init_lib} | StrOutputParser()

result = chain.invoke({{
{invoke_lines}
}})
print(result)
""", language="python")

    if run_btn("🔗 Run with LangChain Chain", key=f"lib_lc_{selected}"):
        try:
            if get_backend() == "Ollama":
                from langchain_community.chat_models import ChatOllama
                from langchain_core.prompts import ChatPromptTemplate as LCTemplate
                from langchain_core.output_parsers import StrOutputParser
                lc_chain = (
                    LCTemplate.from_messages([
                        ("system", "You are an expert data engineering assistant at Sigma DataTech."),
                        ("human", "{filled_prompt}"),
                    ])
                    | ChatOllama(model=get_ollama_model())
                    | StrOutputParser()
                )
                with st.spinner(f"LangChain → {get_ollama_model()} running…"):
                    t0 = time.perf_counter()
                    lc_text = lc_chain.invoke({"filled_prompt": filled})
                    lc_elapsed = time.perf_counter() - t0
            elif get_backend() == "Gemini":
                st.info("💡 Gemini LangChain needs `pip install langchain-google-genai`. Running via direct Gemini API.")
                with st.spinner(f"Gemini ({get_gemini_model()}) running…"):
                    t0 = time.perf_counter()
                    lc_text, _ = call_gemini(
                        get_gemini_key(),
                        "You are an expert data engineering assistant at Sigma DataTech.",
                        [{"role": "user", "content": filled}],
                        model=get_gemini_model(), max_tokens=1600,
                    )
                    lc_elapsed = time.perf_counter() - t0
            else:
                from langchain_anthropic import ChatAnthropic
                from langchain_core.prompts import ChatPromptTemplate as LCTemplate
                from langchain_core.output_parsers import StrOutputParser
                lc_chain = (
                    LCTemplate.from_messages([
                        ("system", "You are an expert data engineering assistant at Sigma DataTech."),
                        ("human", "{filled_prompt}"),
                    ])
                    | ChatAnthropic(api_key=get_api_key(), model_name=get_claude_model(), max_tokens=1600)
                    | StrOutputParser()
                )
                with st.spinner("LangChain → Claude running…"):
                    t0 = time.perf_counter()
                    lc_text = lc_chain.invoke({"filled_prompt": filled})
                    lc_elapsed = time.perf_counter() - t0

            st.markdown("#### 📤 LangChain Output")
            st.markdown(lc_text)
            st.metric("Response time", f"{lc_elapsed:.1f}s")
            notice_box(
                "You just ran: <b>PromptTemplate → Model → StrOutputParser</b>. "
                "The output is the same as the direct call — but this code is production-ready. "
                "Change a variable value above and run again — the chain re-fills automatically. "
                "This is exactly how your prompt library would run inside a real pipeline."
            )
        except Exception as e:
            st.error(f"LangChain error: {e}")
            st.info("Make sure langchain-community is installed: `pip install langchain-community`")

    st.divider()

    st.markdown("### 📤 Export Your Prompt Library")
    col_exp, col_prev = st.columns([1, 2])

    with col_exp:
        st.markdown("When all 6 prompts are tested, generate and download your library.")
        if st.button("📥 Generate de_prompt_library.md", key="export_lib"):
            md = generate_library_md(st.session_state.lib_prompts)
            st.session_state["lib_md"] = md
            st.success("✅ Ready to download!")

        if "lib_md" in st.session_state:
            st.download_button(
                label="⬇️ Download de_prompt_library.md",
                data=st.session_state["lib_md"],
                file_name="de_prompt_library.md",
                mime="text/markdown",
            )

    with col_prev:
        if "lib_md" in st.session_state:
            with st.expander("Preview file"):
                st.code(st.session_state["lib_md"][:2000] + "\n…", language="markdown")

    st.divider()
    st.markdown("### ✅ Before You Leave — Checklist")
    checks = [
        "Tested SQL Generation — output matched my preferred style",
        "Tested Schema Documentation — JSON parsed successfully",
        "Tested Error Explanation — answer was specific, not generic",
        "Tested Data Quality Rules — at least one 'critical' rule in output",
        "Tested Pipeline Description — all 7 sections present",
        "Tested dbt Model Stub — schema.yml included dbt tests",
        "Exported de_prompt_library.md",
        "Committed de_prompt_library.md to GitHub",
    ]
    for c in checks:
        st.checkbox(c, key=f"chk_{c}")


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════════════════════
def main():
    module = render_sidebar()

    if   "Introduction"  in module: page_home()
    elif "Shot-Based"    in module: page_shot_prompting()
    elif "Chain-of"      in module: page_cot_react()
    elif "Role"          in module: page_role_prompting()
    elif "NL"            in module: page_nl_sql()
    elif "Structured"    in module: page_structured_output()
    elif "Context"       in module: page_context_engineering()
    elif "LangChain"     in module: page_langchain_vs_sdk()
    elif "Prompt"        in module: page_de_prompt_library()


if __name__ == "__main__":
    main()
