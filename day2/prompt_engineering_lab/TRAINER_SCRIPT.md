# Day 2 — Prompt Engineering Lab
# TRAINER SCRIPT — Follow This Top to Bottom

---

## BEFORE CLASS STARTS (10 minutes)

1. Open Terminal → run:
   python -m streamlit run app.py
   Browser opens at http://localhost:8501

2. In the sidebar → set YOUR setup to: ☁️ Claude API (Trainer)
   Enter your Anthropic API key → click Test Connection → confirm green tick

3. Keep model on: claude-haiku-4-5-20251001 (fast, cheap)

4. Tell students to open the same URL on their laptops

   **BACKEND OPTIONS FOR STUDENTS (pick one):**

   | Backend | Who | What to do |
   |---------|-----|------------|
   | ✨ Gemini (default) | Students | Select Gemini → paste Google AI Studio key (aistudio.google.com → Get API Key, free with student account) → pick gemini-3-flash-preview |
   | 🖥️ Ollama Local | Students with local setup | Select Ollama → no key needed → confirm qwen2.5:7b is running |
   | ☁️ Claude API | Trainer only | Enter Anthropic key |

   Recommended for students: **Gemini** — free, no install, works immediately.

5. If students use Ollama, confirm it is running:
   Open a terminal → type: ollama list
   Should show qwen2.5:7b in the list

---

## INTRODUCTION (5 minutes)
### Sidebar → click 🏠 Introduction

SHOW students the screen. SAY:

   "This is your lab for today. 8 modules — each one is a mini-experiment.
   You read the concept, you see the prompt being built,
   you click Run, and you compare what changes.
   The coloured boxes you'll see throughout are:
   Green = the Role we give the AI (who it pretends to be)
   Blue = the actual Question we ask
   This colour coding is consistent across every module."

POINT at the module list on the right. SAY:
   "We will go through all 8 together. For each one I demo first, then you try."

---

## MODULE 1 — Shot-Based Prompting (20 minutes)
### Sidebar → click 1️⃣ Shot-Based Prompting

READ the mission banner aloud. SAY:
   "A 'shot' is an example you embed in your prompt.
   Today's experiment: we ask the AI the exact same business question 3 times.
   The question never changes. Only the number of examples we give changes.
   Watch what happens to the output each time."

---

### Step 1 — Show the anatomy tabs (5 min)

CLICK tab: 📖 Zero-shot explained
SHOW the green and blue boxes. SAY:
   "Zero-shot — just ask. No examples. The AI uses only its training.
   Like asking a stranger for directions — you get a generic answer."

CLICK tab: 📖 One-shot explained
SHOW how the blue USER box is now bigger. SAY:
   "One-shot — we show ONE example before the question.
   The AI copies that style. Like giving a new employee one sample report."

CLICK tab: 📖 Few-shot explained
SAY:
   "Few-shot — 2 to 3 examples. The AI locks on to your exact standards.
   This is what you use for production SQL at your company."

---

### Step 2 — Live Experiment (10 min)

CLICK tab: 🔬 Live Experiment

SHOW the DE Task text box. SAY:
   "This is the business question. It will NOT change across all 3 experiments.
   Read it — customers with 3+ orders in 90 days, show email and total spend."

CLICK: Zero-shot radio button
POINT at the green and blue boxes below. SAY:
   "Look at what gets sent to the AI — a short role and just the raw question.
   No examples."
CLICK: 🚀 Run — See the Output
WAIT for response. SAY:
   "Notice: did it use the sigma. prefix? Did it add comments?
   Probably not. It just answered generically."

CLICK: One-shot radio button
SHOW how the blue box now has an EXAMPLE section. SAY:
   "Same question — but now we show it one example first.
   Notice the USER box grew. We added a sample SQL before the actual question."
CLICK: 🚀 Run
SAY: "Did the format improve? More consistent with our standards?"

CLICK: Few-shot radio button
CLICK: 🚀 Run
SAY:
   "Same question. Three times. Only the packaging changed.
   This is shot-based prompting — more examples = stronger pattern lock-in."

ASK STUDENTS: "Which one would you trust to send to production?"

---

## MODULE 2 — Chain-of-Thought (15 minutes)
### Sidebar → click 🧠 Chain-of-Thought

READ the mission banner. SAY:
   "Without Chain-of-Thought, the AI jumps to an answer like a doctor
   guessing your diagnosis in 2 seconds. With CoT, it examines the problem
   properly first. Same question — dramatically different quality."

---

### Chain-of-Thought tab (8 min)

MAKE SURE toggle reads: 🧠 Enable step-by-step thinking = OFF
CLICK: 🚀 Run
WAIT for response. SAY:
   "Generic tips. Increase memory. Use partitioning. You've seen this before.
   Not wrong — but not specific to our actual problem."

CLICK the toggle to turn CoT ON
SHOW how the blue USER box now ends with numbered reasoning steps. SAY:
   "We added 4 instructions: what are the causes, what data to gather,
   most probable cause, fix steps in priority order.
   The AI now MUST reason before answering."
CLICK: 🚀 Run
SAY: "See the difference — ordered, specific, actionable.
   Check the token count — CoT costs maybe 200 extra tokens.
   Worth it? Almost always yes for complex problems."

ASK: "Would you use CoT for a simple question like 'Write SQL for top 5 customers'?
   No — it's overkill. Use it for debugging, architecture decisions, root cause analysis."

---

### ReAct tab (7 min)

CLICK tab: 🔁 ReAct Debugging

READ the Thought → Action → Observation loop explanation. SAY:
   "ReAct is how a senior engineer actually debugs production incidents.
   Not guessing — systematically narrowing down the problem.
   Great for building AI-powered runbooks."

SELECT from dropdown: dbt model failing with 'relation does not exist'
   (students have probably seen this error)
CLICK: 🔬 Debug This Incident
WAIT. SAY while waiting: "Count the Thought/Action/Observation cycles."
AFTER response: "How many cycles did it go through?
   Notice how each cycle narrows the problem before the final answer."

---

## MODULE 3 — Role Prompting (15 minutes)
### Sidebar → click 👤 Role Prompting

SAY:
   "Same question — completely different answer — depending on who you ask.
   The green ROLE box defines the expert. We're going to ask the same
   question to two very different experts and compare."

---

### Single role demo (7 min)

DROPDOWN: select Sceptical Tech Lead (challenges assumptions)
SHOW the info box on the right. SAY:
   "This expert challenges everything. Pushes back. Surfaces risks.
   Let's ask: Should we migrate from Airflow to Prefect?"
SHOW the green and blue prompt boxes. SAY:
   "Look — the ROLE (green) changed completely. The QUESTION (blue) is the same."
CLICK: 🚀 Ask This Expert
SAY: "Notice the tone — pushback, hard questions, risks surfaced.
   Now change to Junior Developer Explainer and run the same question."

DROPDOWN: change to Junior Developer Explainer
CLICK: 🚀 Ask This Expert
SAY: "Completely different advice. Same question. Same AI.
   Only the role changed. This is why the system prompt is so powerful."

---

### Side-by-side comparison (8 min)

SCROLL DOWN to Side-by-Side section
SET Role A: Senior Data Engineer
SET Role B: Sceptical Tech Lead
CLICK: 🔬 Ask Both Experts
WHILE WAITING: "Same question to both at the same time. Watch for differences
   in priorities, tone, and what they think matters."
AFTER response: "Which answer is more useful for a Monday morning
   architecture meeting? Which expert would you consult before
   presenting a design to your CTO?"

ASK STUDENTS TO TRY: "You try — pick two roles, type your own question,
   run both. You have 3 minutes."

---

## MODULE 4 — NL ↔ SQL (15 minutes)
### Sidebar → click 🔄 NL ↔ SQL

SAY:
   "This is the most immediately useful module for your daily work.
   Type a business question in plain English — get SQL back.
   The secret ingredient: always give the AI your table structure first."

---

### English → SQL tab (8 min)

CLICK tab: 🔤 English → SQL
SHOW the Schema box. SAY:
   "This is the table structure — the DDL. Without this, the AI invents
   table names and gets it wrong. This is called schema grounding."

READ the business question aloud. CLICK: ⚡ Generate SQL
SHOW the output. SAY: "Copy-paste ready SQL — with comments and proper formatting.
   This took 5 seconds. Manually? 20 minutes."

NOW DEMONSTRATE SCHEMA GROUNDING LESSON:
SELECT ALL text in the Schema box → DELETE it → leave it empty
CLICK: ⚡ Generate SQL
SAY: "Look at the table names it invented — customer_data, transactions, purchases.
   None of those exist. This is why schema grounding is non-negotiable."
RE-PASTE the schema back. Important: restore it before moving on.

---

### SQL → Plain English tab (7 min)

CLICK tab: 🔁 SQL → Plain English
SHOW the complex SQL query. SAY:
   "This query uses CTEs, window functions, PERCENT_RANK.
   Can you explain this to your manager in 30 seconds? No.
   Can the AI? Yes — and it adjusts the explanation for who's listening."

SELECT: Business Analyst (no SQL knowledge)
CLICK: 📖 Explain This SQL
AFTER response: "Plain English — zero SQL terms."

CHANGE TO: Data Architect (full technical + performance detail)
CLICK: 📖 Explain This SQL
SAY: "Same SQL — completely different explanation.
   Use case: auto-document your entire dbt repository overnight."

---

## MODULE 5 — Structured Output (12 minutes)
### Sidebar → click 📋 Structured Output

SAY:
   "AI output is messy text by default. If your pipeline calls
   json.loads() on the response and the AI added one extra sentence —
   your pipeline crashes at 3 AM.
   This module teaches you to force clean, parseable output every time."

---

### JSON Output tab (7 min)

SHOW the table description and JSON schema boxes. SAY:
   "We tell the AI exactly what structure we want — and say
   'Return ONLY valid JSON. Nothing else.'"
SHOW the green prompt boxes. POINT to the ROLE. SAY:
   "Notice the Role says: CRITICAL: Return ONLY valid JSON. No markdown.
   No explanation. That's the key instruction."
CLICK: ⚡ Generate JSON
SHOW both panels — raw output and the green ✅ Valid JSON panel. SAY:
   "The app automatically tests if Python can parse it.
   Green = your pipeline can use this. Red = it would crash."

ASK: "What happens if the AI adds one sentence before the JSON?
   Let's see." — CLICK tab: 🔧 Production Pattern
SAY: "This retry pattern catches parse failures and sends the error
   back to the AI. It fixes itself. Use this in every production pipeline."

---

### YAML Output tab (5 min)

CLICK tab: 📄 YAML Output
READ the pipeline description. CLICK: ⚡ Generate YAML
SAY: "Describe a pipeline in plain English — get Airflow YAML config.
   Change the schedule, add a Slack alert, change the destination —
   re-run. Takes 10 seconds instead of 30 minutes of config editing."

---

## MODULE 6 — Context Engineering (12 minutes)
### Sidebar → click 🗃️ Context Engineering

SAY:
   "Context window = the whiteboard the AI can see.
   Claude's whiteboard holds 200,000 tokens — about 150,000 words.
   Everything you send must fit on that whiteboard.
   When you have 500 tables, you need a strategy."

---

### Token Counter tab (5 min)

SHOW the default schema in the text box.
POINT to the metrics on the right. SAY:
   "This schema uses about 400 tokens — tiny.
   But paste in a 200-table enterprise schema and you're at 20,000 tokens.
   This tool shows you how much space you're using."

DRAG the Budget Planner sliders. SAY:
   "System prompt, schema, conversation history, current question —
   they all eat from the same 200K budget. Plan before you build."
DRAG history slider up until the progress bar goes red. SAY:
   "Hit 80% — warning fires. This is what happens in long conversations."

---

### Conversation Memory tab (5 min)

CLICK tab: 💬 Conversation Memory
TYPE: I have a customers table with id, name, email and tier columns
CLICK: Send
WAIT for response.
TYPE: Write a dedup query for it — remove duplicate emails
CLICK: Send
AFTER response: "It remembered the table from the previous message.
   But notice the token counter growing with each turn.
   The AI doesn't have a 'session' — your code sends the full history every call.
   That's why long conversations get expensive."

CLICK tab: 🛠️ Strategies
SHOW the code. SAY:
   "Strategy 1 — compress your schema. Instead of full DDL: 500 lines,
   write compact notation: 1 line. 10x cheaper.
   Strategy 5 — Prompt Caching: Anthropic caches your schema for 5 minutes.
   Subsequent calls cost 90% less. Use this for production pipelines."

---

## MODULE 7 — LangChain vs SDK (10 minutes)
### Sidebar → click 🔧 LangChain vs SDK
### NOTE: Both trainer AND students can run everything in this module. Ollama users use Qwen; trainer uses Claude.

SAY:
   "Two ways to call the same AI. We'll see both running side by side — and
   you'll build and run a real LangChain chain yourself, not just read code."

READ the 'What is LangChain?' section on screen. SAY:
   "Without LangChain — 6 lines of manual code for every call.
   With LangChain — one line: template | model | parser.
   Same output. But the LangChain version scales to 1,000 tables without changing your code."

SHOW the 3 Building Blocks panel on the right. SAY:
   "Block 1: PromptTemplate — the {placeholder} template you just saw.
   Block 2: ChatOllama or ChatAnthropic — the model connector, swap in one line.
   Block 3: StrOutputParser — strips the API wrapper, gives you a clean string."

SHOW the chain anatomy code block. SAY:
   "The pipe operator | connects them. Output of left becomes input of right.
   template fills variables → model runs → parser returns clean text.
   This is it. This is the whole pattern."

---

### PromptTemplate Builder tab (5 min)

CLICK tab: 🧩 PromptTemplate Builder
SHOW the template text area with {role}, {table_name}, {task}, {output_format} placeholders. SAY:
   "Look at the variables detected — green box shows them automatically.
   These {curly brace} placeholders are the LangChain PromptTemplate syntax.
   You edit the values on the right — the template re-fills instantly."

POINT to the 'Equivalent Python code' block. SAY:
   "This is the EXACT code that runs when you click the button.
   Notice it matches your backend — Ollama users see ChatOllama, I see ChatAnthropic."

CLICK: 🚀 Run with LangChain Chain
WAIT for response. SAY:
   "You just executed: PromptTemplate → ChatOllama → StrOutputParser.
   A real LangChain chain — not a simulation."

ASK STUDENTS: "Now change one variable — like the task — and run again.
   Same chain, different data. That's the whole point of PromptTemplate."

---

### Direct vs LangChain tab (3 min)

CLICK tab: ⚡ Direct vs LangChain Live
CLICK: ⚡ Run Both — Compare Side by Side
WAIT for both columns. SAY:
   "Same output. LangChain adds a tiny overhead.
   But look at what you gain: batch 50 tables with .batch(),
   swap from Qwen to Claude by changing one line, stream tokens with .stream()."

CLICK tab: 📊 When to Use Which?
SAY: "Simple script → direct API. Production pipeline → LangChain. Screenshot this table."

---

## MODULE 8 — Prompt Library (45 minutes)
### Sidebar → click 📖 Prompt Library
### TRAINER DEMO: 5 minutes. Then students work independently for 40 minutes.

SAY:
   "This is your deliverable for today — your personal DE Prompt Library.
   6 real production prompts. You test each one, customise it to your style,
   and export a markdown file you can use at work."

TRAINER DEMO:
SELECT from dropdown: 1. SQL Generation
SHOW the template with {variable} placeholders. SAY:
   "This is the starter template. The variables on the right fill it in.
   Notice the {curly brace} syntax — same as LangChain PromptTemplate."
CHANGE one variable — e.g. change the nl_request to something your own.
CLICK: 🚀 Test This Prompt
SHOW the output.

SCROLL DOWN to the LangChain section. SAY:
   "Now look below — there is a second button: 'Run with LangChain Chain'.
   The code block shows the production Python for this exact prompt.
   Variables auto-fill from what you entered above."
CLICK: 🔗 Run with LangChain Chain
WAIT for response. SAY:
   "Same output — but now it ran through a real LangChain chain.
   This is how you'd build a pipeline that documents all 500 Sigma tables overnight."

CLICK: ↩ Reset to default. SAY: "Reset restores the original — always start fresh."
CLICK: 📥 Generate de_prompt_library.md → ⬇️ Download
OPEN the downloaded file. SAY:
   "This is what you're building. Test all 6 prompts.
   For at least 2 of them, also click the LangChain button so you practice that too.
   Customise at least 2 templates to your own style.
   Then export and commit to GitHub before end of day."

HAND TO STUDENTS — they work independently.
CIRCULATE every 10 minutes. Common issues:
   - "Nothing happens when I click Run" → check Ollama is running (ollama serve)
   - "I can't find the download button" → they must click Generate first, then Download appears
   - "The output doesn't look right" → ask them to edit the template and re-run
   - "LangChain button gives error" → run: pip install langchain-community in terminal

AT 10 MINUTES REMAINING: "Wrap up whatever prompt you're on.
   Click Generate and Download now. Then commit to GitHub."

---

## QUIZ (20 minutes)
### Switch to Day2_Slides.pptx → go to Quiz slides (Slide 30)

SAY: "10 questions. 60 seconds each. Write answers on paper — team name at top."
READ each question aloud. Give 60 seconds. Move to next.
After Q10 — collect papers.
GO TO: Slide 35 (Quiz Answers)
READ answers + 1-line explanation for each.
Teams self-score. Call out scores. Update leaderboard.

---

## END OF DAY (5 minutes)
### Slides → Day 2 Complete slide

SAY: "Three things you can do from tomorrow:
   1. Any SQL task — use few-shot prompting with your team's examples
   2. Any debugging task — enable Chain-of-Thought
   3. Any repetitive documentation task — use your prompt library

Tonight's homework: add a 7th prompt to your library — something from your
own DE experience that we didn't cover. Post the commit by 9 AM tomorrow."

---

## QUICK REFERENCE — Things That Go Wrong

| Problem | What happened | Fix |
|---------|--------------|-----|
| Student clicks Run, nothing happens | Ollama not running | Terminal → ollama serve |
| "Connection refused" error in app | Same as above | ollama serve |
| Response is very slow | Qwen 7b on low RAM | Normal — can take 30-60 seconds |
| Download button not showing | They skipped Generate step | Click Generate first, then Download appears |
| JSON shows red ❌ | Qwen added extra text outside JSON | Normal for smaller models — that's the lesson |
| Module 7 shows "Trainer Demo" for student | Correct behaviour | Tell them to watch your screen |
| Streamlit app not opening | Port conflict | Try: streamlit run app.py --server.port 8502 |
