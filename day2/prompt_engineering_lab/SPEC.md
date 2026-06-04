# SPEC — Day 2 Lab: Prompt Engineering for Data Engineers
**Version:** 1.0 — Awaiting approval  
**Bootcamp:** GenAI for Data Engineering, Sigmoid Bangalore, May 2026  
**Audience:** ~35–40 final-year B.Tech interns  

---

## 1. Purpose & Learning Objectives

Students will use this app to understand and practise 8 core prompt engineering techniques
used by Data Engineers in production. The app teaches by doing — every concept has a live
Claude call that students run themselves.

| Syllabus bullet | Covered in module |
|-----------------|-------------------|
| Zero-shot, one-shot, few-shot | Module 1 |
| Chain-of-thought & ReAct | Module 2 |
| Role prompting | Module 3 |
| NL→SQL & SQL→NL | Module 4 |
| Structured output: JSON / YAML | Module 5 |
| Context engineering: tokens & state | Module 6 |
| LangChain PromptTemplate + Claude SDK | Module 7 |
| DE Prompt Library (deliverable) | Module 8 |

---

## 2. Usage Modes

| Mode | Who | How |
|------|-----|-----|
| **Demo** | Trainer projects on Smart TV, drives the app | Presenter Mode ON — hides instruction panels |
| **Hands-on** | Each student opens URL on their own laptop | Presenter Mode OFF — full guided view |

Both modes use the same deployed URL. Trainer toggles Presenter Mode at the top of the sidebar.

---

## 3. Technical Stack

| Component | Library | Version |
|-----------|---------|---------|
| UI | streamlit | ≥ 1.35 |
| Claude SDK | anthropic | ≥ 0.28 |
| LangChain core | langchain-core | ≥ 0.2 |
| LangChain Anthropic | langchain-anthropic | ≥ 0.1.15 |
| Env vars | python-dotenv | ≥ 1.0 |
| Tests | pytest + unittest.mock | stdlib mock |

Python: 3.10+

---

## 4. File Structure

```
day2/prompt_engineering_lab/
├── app.py                  ← main Streamlit app (new build)
├── app_v1.py               ← previous build kept as backup
├── requirements.txt
├── .env.example
├── SPEC.md                 ← this document
└── tests/
    ├── __init__.py
    └── test_app.py
```

---

## 5. Global Layout

```
┌─ SIDEBAR (240px) ──────────┐  ┌─ MAIN AREA ──────────────────────────────┐
│                            │  │                                           │
│  🧪 Prompt Engineering Lab │  │  [Module content — see module specs]      │
│  Day 2 · Sigmoid Bangalore │  │                                           │
│                            │  │                                           │
│  ── Presenter Mode ──────  │  │                                           │
│  [ ] Presenter Mode        │  │                                           │
│                            │  │                                           │
│  ── API Key ─────────────  │  │                                           │
│  [●●●●●●●●●●] (password)  │  │                                           │
│  [ Test Connection ]       │  │                                           │
│  ✓ Connected · Haiku       │  │                                           │
│                            │  │                                           │
│  ── Model ───────────────  │  │                                           │
│  ○ Haiku (recommended)     │  │                                           │
│  ○ Sonnet                  │  │                                           │
│                            │  │                                           │
│  ── Navigate ────────────  │  │                                           │
│  🏠 Introduction           │  │                                           │
│  1️⃣ Shot-Based Prompting   │  │                                           │
│  🧠 CoT & ReAct            │  │                                           │
│  👤 Role Prompting         │  │                                           │
│  🔄 NL ↔ SQL               │  │                                           │
│  📋 Structured Output      │  │                                           │
│  🗃️ Context Engineering    │  │                                           │
│  🔧 LangChain vs SDK       │  │                                           │
│  📖 DE Prompt Library      │  │                                           │
│                            │  │                                           │
└────────────────────────────┘  └───────────────────────────────────────────┘
```

---

## 6. Presenter Mode

**Toggle:** Checkbox in sidebar — `st.session_state.presenter_mode`

| Element | Presenter OFF (student) | Presenter ON (demo) |
|---------|------------------------|---------------------|
| Concept box | Visible | Hidden |
| "What to do" instruction panel | Visible | Hidden |
| Prompt anatomy explanation | Visible | Hidden |
| Prompt preview expander | Visible | Collapsed & locked |
| Run button | Visible | Visible |
| Output area | Visible | Visible |
| Token metrics | Visible | Visible |
| Tab labels | Visible | Visible |

Presenter Mode only hides explanatory/instructional elements — all interactive and output elements remain fully visible.

---

## 7. API Key Management

- Input: `st.text_input("Anthropic API Key", type="password")` in sidebar
- Stored: `st.session_state.api_key`
- **Test Connection button:** makes a minimal `client.messages.create` call (5-token max) to verify the key
- Connection status displayed below: `✓ Connected · claude-haiku-4-5-20251001` or `✗ Invalid key`
- Both the Anthropic SDK and LangChain `ChatAnthropic` receive the key from session state
- Key is never written to disk or logged

---

## 8. Shared Components

### 8a. Concept Box
Blue left-border card. Shown only when Presenter Mode = OFF.
```
┌── blue left border ──────────────────────────┐
│ Bold title sentence.                          │
│ Supporting explanation 1–2 lines.             │
│ For Data Engineers: practical use case.       │
└───────────────────────────────────────────────┘
```

### 8b. Prompt Preview Expander
Label: `👁️ Exact prompt sent to Claude`  
Shows two labelled blocks:
```
🟢 SYSTEM
┌──────────────────┐
│ system text here │
└──────────────────┘

🔵 USER
┌──────────────────┐
│ user text here   │
└──────────────────┘
```
Hidden in Presenter Mode.

### 8c. Output + Token Metrics
After every Run button:
```
┌─ Output (70% width) ──────┐  ┌─ Tokens (30%) ──┐
│ model response rendered   │  │ Input:   1,234   │
│ as markdown               │  │ Output:    456   │
│                           │  │ Total:   1,690   │
│                           │  │ Time:    1.2 s   │
└───────────────────────────┘  └─────────────────┘
```
Response time measured with `time.perf_counter()`.

### 8d. Run Button
Label: `🚀 Run`  
Disabled (greyed out) when `api_key` is empty.  
Shows `st.spinner("Calling Claude…")` while waiting.

### 8e. Error Display
On API failure: `st.error("API error: {message}")` — full error message visible to student so they can diagnose wrong keys, quota exhaustion, etc.

---

## 9. Module Specifications

---

### Module 0 — Introduction

**Purpose:** Orient students to the app and the day's learning path.

**Layout:**
```
Title: 🧪 Prompt Engineering for Data Engineers
Subtitle: Day 2 Lab · Sigma DataTech

┌─ col 60% ─────────────────────┐  ┌─ col 40% ──────────────────┐
│ Mission Briefing (markdown)   │  │ Module list (8 items)       │
│                               │  │                             │
│ How to use this app           │  │ Deliverable callout box:    │
│ (4-step instruction)          │  │ "Export de_prompt_library   │
│                               │  │  .md by end of day"        │
│ Colour legend for prompt      │  │                             │
│ anatomy (🟢🔵🟡🟣)           │  │                             │
└───────────────────────────────┘  └─────────────────────────────┘
```

**Presenter Mode:** Mission briefing visible; instruction panel hidden.

---

### Module 1 — Shot-Based Prompting

**Concept:** Zero-shot / One-shot / Few-shot — more examples = stronger pattern enforcement.

**Tabs:** `Zero-shot` | `One-shot` | `Few-shot` | `🔬 Live Comparison`

**Tabs 1–3 (anatomy panels):**
```
┌─ Left col 40% ──────────────────┐  ┌─ Right col 60% ────────────────────┐
│ Table: Part / What it does      │  │ Colour-coded prompt block          │
│ (system, examples, user)        │  │ 🟢 SYSTEM: ...                     │
│                                 │  │ 🟡 EXAMPLE: ...                    │
│ Caption: when to use this       │  │ 🔵 USER: ...                       │
└─────────────────────────────────┘  └────────────────────────────────────┘
```
These tabs are READ-ONLY — no inputs, no Run button. Anatomy explanation only.

**Tab 4 — Live Comparison:**
```
┌─ Inputs ────────────────────────────────────────────┐
│ text_area: "DE Task" (pre-filled, editable)          │
│ radio: Strategy = Zero-shot | One-shot | Few-shot    │
└──────────────────────────────────────────────────────┘
[👁️ Prompt preview expander]
[🚀 Run]
┌─ Output 70% ─────────┐  ┌─ Token metrics 30% ──┐
│ model response        │  │ Input / Output / Time │
└───────────────────────┘  └───────────────────────┘
```
Prompt is built internally based on the selected strategy — students do not edit the prompt structure, only the task description.

**Pre-filled task:** "Find customers who placed more than 3 orders in the last 90 days, show email and total spend"

---

### Module 2 — Chain-of-Thought & ReAct

**Concept:** Reasoning before answering. CoT for analysis; ReAct for debugging.

**Tabs:** `Chain-of-Thought` | `ReAct Pattern`

**CoT Tab:**
```
┌─ Side-by-side anatomy ─────────────────────────────────────────┐
│ ❌ Without CoT (left col)    ✅ With CoT (right col)            │
│ code block: direct prompt    code block: step-by-step prompt   │
│ caption: consequence          caption: consequence              │
└────────────────────────────────────────────────────────────────┘
──────────────────────────────
┌─ Live Demo ─────────────────────────────────────┐
│ text_area: DE problem (pre-filled, editable)     │
│ toggle: [ ] Enable Chain-of-Thought             │
└──────────────────────────────────────────────────┘
[👁️ Prompt preview]  [🚀 Run]
[Output + Tokens]
```

**ReAct Tab:**
```
┌─ ReAct loop diagram ────────────────────────────┐
│ THOUGHT → ACTION → OBSERVATION → (repeat) →    │
│ FINAL ANSWER                                    │
└──────────────────────────────────────────────────┘
┌─ Inputs ────────────────────────────────────────┐
│ selectbox: DE scenario (5 pre-set options)      │
└──────────────────────────────────────────────────┘
[👁️ Prompt preview]  [🚀 Run]
[Output + Tokens]
```
Scenario selectbox is pre-set; students choose from list, cannot type custom.

---

### Module 3 — Role Prompting

**Concept:** Same question, different persona → different expertise, tone, focus.

**Layout:**
```
┌─ Top: Single Role Demo ────────────────────────────────────────────┐
│ col 50%: selectbox (5 roles) + text_area question (editable)       │
│ col 50%: active role context card + prompt anatomy diagram         │
│ [🚀 Ask]                                                           │
│ [Output + Tokens]                                                  │
└────────────────────────────────────────────────────────────────────┘
──────────────────────────────────
┌─ Bottom: Side-by-Side Comparison ──────────────────────────────────┐
│ text_input: comparison question (pre-filled, editable)             │
│ col 50%: selectbox Role A | col 50%: selectbox Role B             │
│ [🔬 Compare Both]                                                  │
│ col 50%: Response A     | col 50%: Response B                     │
└────────────────────────────────────────────────────────────────────┘
```

**6 pre-set roles:**
1. Senior Data Engineer (dbt + Airflow expert)
2. Cloud Architect (cost-optimisation focus)
3. Data Quality Engineer (testing advocate)
4. Sceptical Tech Lead (challenges assumptions)
5. Junior Developer Explainer (plain language)
6. Junior Data Engineer (learning the basics, asks clarifying questions)

---

### Module 4 — NL ↔ SQL

**Concept:** Schema grounding is mandatory. Without it, the model hallucinates table names.

**Tabs:** `🔤 NL → SQL` | `🔁 SQL → NL`

**NL → SQL Tab:**
```
┌─ col 55% ──────────────────────┐  ┌─ col 45% ──────────────────────────┐
│ text_area: Schema DDL          │  │ Prompt anatomy flow diagram:        │
│ (pre-filled Sigma schema,      │  │ SYSTEM (dialect + rules)            │
│  editable)                     │  │   ↓                                 │
│                                │  │ USER: Schema DDL ← grounding        │
│ text_area: Business question   │  │       Business question             │
│ (pre-filled, editable)         │  │       Output format                 │
│                                │  │                                     │
│ selectbox: SQL dialect         │  │ "Without schema → hallucination"    │
└────────────────────────────────┘  └─────────────────────────────────────┘
[👁️ Prompt preview]  [⚡ Generate SQL]
[Output + Tokens]
```

**SQL → NL Tab:**
```
┌─ col 55% ──────────────────────┐  ┌─ col 45% ──────────────────────────┐
│ text_area: SQL to explain      │  │ Real DE use cases:                  │
│ (pre-filled complex CTE,       │  │ - dbt model auto-docs               │
│  editable)                     │  │ - Glue catalog descriptions         │
│                                │  │ - Stakeholder explainers            │
│ selectbox: Audience            │  │                                     │
│ (4 options)                    │  │ Code snippet: auto-doc pattern      │
└────────────────────────────────┘  └─────────────────────────────────────┘
[👁️ Prompt preview]  [📖 Explain SQL]
[Output + Tokens]
```

---

### Module 5 — Structured Output

**Concept:** Enforce JSON/YAML for downstream pipeline consumption. Parse + validate + retry.

**Tabs:** `JSON Output` | `YAML Output` | `Production Pattern`

**JSON Tab:**
```
┌─ col 50% ─────────────────────┐  ┌─ col 50% ──────────────────────────┐
│ selectbox: Task type           │  │ text_area: JSON schema to enforce   │
│ text_area: Table description   │  │ (pre-filled, editable)              │
│ (pre-filled, editable)         │  │                                     │
└────────────────────────────────┘  └─────────────────────────────────────┘
[👁️ Prompt preview]  [⚡ Generate JSON]
┌─ Raw output col ──────────────┐  ┌─ Parsed & validated col ───────────┐
│ st.code (raw model text)      │  │ ✅ Valid JSON  →  st.json(parsed)   │
│                               │  │ ❌ Invalid  →  error + explanation  │
└────────────────────────────────┘  └─────────────────────────────────────┘
```

**YAML Tab:** Same layout, YAML schema, pipeline config output.

**Production Pattern Tab:** Read-only code block — parse + retry pattern in Python. No Run button.

---

### Module 6 — Context Engineering

**Concept:** Token budget, conversation state, strategies for large schemas.

**Tabs:** `Token Counter` | `Conversation State` | `Strategies`

**Token Counter Tab:**
```
┌─ col 60% ────────────────────────────────────┐  ┌─ col 40% ──────────┐
│ text_area: paste any text                    │  │ Metric: Characters  │
│ (pre-filled with Sigma schema DDL, editable) │  │ Metric: Est. tokens │
│                                              │  │ Metric: % of 200K   │
│                                              │  │                     │
│                                              │  │ Rules of thumb      │
└──────────────────────────────────────────────┘  └─────────────────────┘
── Budget Planner ──────────────────────────────────────────────────────
4 sliders: System prompt | Schema | History | Query
Progress bar + 3 metrics: Total / % Used / Remaining
Status: ✅ healthy | ⚠️ high | 🔴 critical
```

**Conversation State Tab:**
```
Multi-turn chat demo (stateful within session)
text_input + [Send] [🗑️ Clear]
Conversation history displayed message by message
Token progress bar updating after each turn
Caption: "~X tokens (Y% of 200K context)"
```

**Strategies Tab:** Read-only — 5 code patterns. No Run button.

---

### Module 7 — LangChain vs SDK (Side-by-Side)

**Concept:** Same prompt, two execution paths — measure and compare.

**Tabs:** `Template Builder` | `⚡ SDK vs LangChain` | `Why Chains?`

**Template Builder Tab:**
```
┌─ col 50% ──────────────────────────────────┐  ┌─ col 50% ─────────────────────────────┐
│ text_area: template with {variables}        │  │ Detected variables listed             │
│ (pre-filled DE example, editable)           │  │ text_input per variable (pre-filled,  │
│                                             │  │ editable)                             │
└─────────────────────────────────────────────┘  └────────────────────────────────────────┘
── Filled prompt preview ──
── Generated LangChain code block (dynamic, updates as vars change) ──
[🚀 Run Template]
[Output + Tokens]
```

**SDK vs LangChain Tab:**
```
text_area: shared prompt / template (pre-filled, editable)
[⚡ Run Both]
┌─ Anthropic SDK col ────────────────┐  ┌─ LangChain Chain col ──────────────┐
│ 🟠 SDK                             │  │ 🟣 LangChain                        │
│ Code: client.messages.create(...)  │  │ Code: template | llm | parser       │
│ ─────────────────────────────────  │  │ ───────────────────────────────────  │
│ Response time: 1.24s               │  │ Response time: 1.31s                │
│ ─────────────────────────────────  │  │ ───────────────────────────────────  │
│ Output: [model response]           │  │ Output: [model response]            │
└────────────────────────────────────┘  └─────────────────────────────────────┘
Observation box: "Both produced the same output. LangChain added Xms overhead.
                  Value is in composability, not raw speed."
```

**Why Chains? Tab:** Read-only comparison table + code examples. No Run button.

---

### Module 8 — DE Prompt Library

**Concept:** Build and export a reusable DE prompt library as the Day 2 deliverable.

**Layout:**
```
── Prompt selector ──────────────────────────────────────────────────────
selectbox: 6 prompts (1–6)
── Selected prompt ──────────────────────────────────────────────────────
┌─ col 50% ─── Template ────────────────┐  ┌─ col 50% ─── Variables ──────────────┐
│ text_area: template text               │  │ text_area per variable               │
│ (pre-filled starter, EDITABLE)         │  │ (pre-filled defaults, EDITABLE)      │
│                                        │  │                                      │
│ [↩ Reset to default]                   │  │                                      │
└────────────────────────────────────────┘  └──────────────────────────────────────┘
── Filled prompt preview ────────────────────────────────────────────────
[👁️ Preview filled prompt]
[🚀 Test This Prompt]
[Output + Tokens]
── Export ───────────────────────────────────────────────────────────────
[📥 Generate de_prompt_library.md]   [⬇️ Download]
── Completion Checklist ─────────────────────────────────────────────────
8 checkboxes (student self-marks)
```

**The 6 prompts:**
1. SQL Generation
2. Schema Documentation → JSON
3. Error Explanation
4. Data Quality Rules → JSON array
5. Pipeline Description → Markdown
6. dbt Model Stub

**Hybrid behaviour:**
- All 6 templates pre-filled as starters
- Students can edit both the template text AND variable values
- `[↩ Reset to default]` button per prompt restores the starter
- Export captures whatever is in the text_areas at time of download — student's edited version

---

## 10. State Management

| Session variable | Type | Purpose |
|-----------------|------|---------|
| `api_key` | str | Anthropic API key |
| `model` | str | Selected model ID |
| `presenter_mode` | bool | Hide/show instructional elements |
| `ctx_msgs` | list | Conversation history for Module 6 |
| `lib_prompts` | dict | Student-edited DE prompt templates |
| `lib_md` | str | Generated library markdown for download |
| `connection_status` | str | "ok" / "error" / "untested" |

---

## 11. Error Handling

| Scenario | Behaviour |
|----------|-----------|
| No API key | Run button disabled; tooltip: "Enter API key in sidebar" |
| Invalid API key | `st.error("Invalid API key — check console.anthropic.com")` |
| Quota exhausted | `st.error("Credit limit reached — top up at console.anthropic.com")` |
| Network timeout | `st.error("Request timed out — retry")` |
| JSON parse failure (Module 5) | Show raw output + red validation error + retry suggestion |
| LangChain call fails (Module 7) | Show SDK result only; flag LangChain error clearly |

---

## 12. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Smart TV readability | Body text ≥ 16px; titles ≥ 28px; high contrast |
| Response time feedback | Spinner shown for all API calls; time displayed in output |
| Self-directed usability | Every module has a "What to do here" panel (hidden in Presenter Mode) |
| No trainer notes | Zero trainer-only content in UI — student-facing only |
| Design | Clean / minimal — no clip art, no gradient boxes, indigo (#4f46e5) accent only |
| Test coverage | All helper functions, all prompt builders, export function — API mocked |

---

## 13. Out of Scope

- User authentication / student tracking
- Persistent storage of student outputs
- Mobile / tablet layout optimisation
- Streaming responses (token-by-token output)
- Any module beyond the 8 listed

---

## Approval Checklist

Before implementation begins, confirm:

- [ ] All 8 modules confirmed (no additions / removals)
- [ ] Presenter Mode behaviour correct
- [ ] API key handling approach correct (individual, visible, Test Connection button)
- [ ] Module 7 side-by-side SDK vs LangChain layout approved
- [ ] Module 8 hybrid (editable starters + reset + export) approved
- [ ] Non-functional requirements accepted

**Sign-off:** _________________________  Date: ___________
