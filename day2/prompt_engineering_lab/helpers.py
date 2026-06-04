"""
Pure functions — zero Streamlit dependency.
All testable via pytest without mocking st.*.
"""

import json
import re
import urllib.request
import urllib.error
from anthropic import Anthropic
from prompts import ROLES

# ── Constants ──────────────────────────────────────────────────────────────────
VALID_SHOT_TYPES = {"Zero-shot", "One-shot", "Few-shot"}

AUDIENCE_INSTRUCTIONS = {
    "Business Analyst (no SQL knowledge)":
        "Explain in plain English with zero SQL terms. Focus on what business question "
        "it answers and what the result rows look like.",
    "Junior Developer (knows basic SQL)":
        "Explain each section. Call out advanced SQL features (window functions, CTEs) "
        "and explain why they are used here.",
    "Product Manager (needs the business so-what)":
        "One sentence on what it does, then focus on what decisions the output enables. "
        "Keep it under 150 words.",
    "Data Architect (full technical + performance detail)":
        "Provide a technical analysis: CTE strategy, window functions, join order, "
        "index and partition implications, and optimisation suggestions.",
}


# ── Token estimation ───────────────────────────────────────────────────────────
def estimate_tokens(text: str) -> int:
    """Rough estimate: 1 token ≈ 4 characters (English text)."""
    return len(text) // 4


# ── Template filler ────────────────────────────────────────────────────────────
def fill_template(template: str, variables: dict) -> str:
    """Replace {key} placeholders with values. Unknown placeholders left intact."""
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result


# ── JSON parser ────────────────────────────────────────────────────────────────
def parse_json_response(text: str) -> tuple:
    """
    Parse a model response as JSON.
    Handles markdown code fences (```json ... ```).
    Returns: (parsed_object | None, is_valid: bool, error_message: str)
    """
    if not text or not text.strip():
        return None, False, "Empty response"

    cleaned = text.strip()

    # Strip markdown fences if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        inner = []
        skip_first = True
        for line in lines:
            if skip_first:
                skip_first = False
                continue
            if line.strip() == "```":
                break
            inner.append(line)
        cleaned = "\n".join(inner).strip()

    try:
        parsed = json.loads(cleaned)
        return parsed, True, ""
    except json.JSONDecodeError as exc:
        return None, False, str(exc)


# ── Shot-based prompt builder ──────────────────────────────────────────────────
def build_shot_prompt(task: str, shot_type: str) -> tuple:
    """
    Build (system, user) for zero / one / few-shot prompting.
    Raises ValueError for unknown shot_type.
    """
    if shot_type not in VALID_SHOT_TYPES:
        raise ValueError(
            f"shot_type must be one of {VALID_SHOT_TYPES}, got '{shot_type}'"
        )

    if shot_type == "Zero-shot":
        system = "You are a SQL expert."
        user = task

    elif shot_type == "One-shot":
        system = (
            "You are a SQL expert who generates production-ready, well-formatted queries."
        )
        user = f"""EXAMPLE:
Q: Top 5 customers by revenue
SQL:
```sql
SELECT
    customer_id,
    SUM(amount) AS total_revenue
FROM orders
GROUP BY customer_id
ORDER BY total_revenue DESC
LIMIT 5;
```

Now write: {task}"""

    else:  # Few-shot
        system = (
            "You are a SQL expert at Sigma DataTech. Match our coding standards exactly."
        )
        user = f"""Study these examples of our SQL style:

EXAMPLE 1:
Q: Daily revenue trend (30 days)
```sql
-- Business: Daily revenue for last 30 days
SELECT
    DATE_TRUNC('day', created_at) AS order_date,
    SUM(amount)                   AS daily_revenue,
    COUNT(DISTINCT customer_id)   AS unique_customers
FROM sigma.orders
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;
```

EXAMPLE 2:
Q: Customers active last quarter
```sql
-- Business: Active customers in last quarter
SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id)  AS order_count,
    SUM(o.amount)      AS total_spend
FROM sigma.customers c
JOIN sigma.orders     o ON c.customer_id = o.customer_id
WHERE o.created_at >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '3 months')
GROUP BY 1, 2
ORDER BY total_spend DESC;
```

Now write: {task}"""

    return system, user


# ── CoT prompt builder ─────────────────────────────────────────────────────────
def build_cot_prompt(problem: str, use_cot: bool) -> tuple:
    """Build (system, user) for chain-of-thought prompting."""
    system = (
        "You are a senior Data Engineer specialising in Spark, distributed systems, "
        "and pipeline debugging."
    )
    if use_cot:
        user = f"""{problem}

Reason through this step by step:
1. What are the most likely root causes?
2. What diagnostic data would you gather first?
3. Given the symptoms, what is the most probable cause?
4. Give fix steps in priority order with exact commands or config values."""
    else:
        user = problem

    return system, user


# ── ReAct prompt builder ───────────────────────────────────────────────────────
def build_react_prompt(scenario: str) -> tuple:
    """Build (system, user) for ReAct debugging pattern."""
    system = """You are a senior Data Engineer debugging a production incident.
Use EXACTLY this ReAct format:

Thought: [what you are reasoning about]
Action: [specific command / query / check you would run]
Observation: [what you would typically find]

Repeat Thought/Action/Observation as needed (3-5 cycles), then:

Final Answer: [root cause in 1 sentence] + [step-by-step fix]"""

    user = f"Debug this production issue using systematic ReAct reasoning: {scenario}"
    return system, user


# ── Role prompt builder ────────────────────────────────────────────────────────
def build_role_prompt(role_name: str, question: str) -> tuple:
    """
    Build (system, user) using a named role from ROLES dict.
    Raises KeyError if role_name not found.
    """
    if role_name not in ROLES:
        raise KeyError(f"Role '{role_name}' not found in ROLES dict")
    return ROLES[role_name], question


# ── NL → SQL prompt builder ────────────────────────────────────────────────────
def build_nl_sql_prompt(schema: str, question: str, dialect: str) -> tuple:
    """Build (system, user) for natural language to SQL translation."""
    system = (
        f"You are a {dialect} SQL expert at Sigma DataTech.\n"
        "Write production-ready queries following these standards:\n"
        "- Schema prefix sigma. on all tables\n"
        "- Use AS keyword for all aliases\n"
        "- CTEs for readability when more than 2 joins\n"
        "- Inline comments for non-obvious business logic\n"
        "Return ONLY the SQL inside a markdown code block."
    )
    user = f"""Schema:
{schema}

Business question:
{question}

Write the SQL."""
    return system, user


# ── SQL → NL prompt builder ────────────────────────────────────────────────────
def build_sql_nl_prompt(sql: str, audience: str) -> tuple:
    """Build (system, user) for SQL to natural language explanation."""
    system = (
        "You are a SQL documentation expert who explains queries clearly to any audience."
    )
    instruction = AUDIENCE_INSTRUCTIONS.get(audience, "Explain this SQL query clearly.")
    user = f"""Explain this SQL query:

```sql
{sql}
```

Audience: {audience}
{instruction}"""
    return system, user


# ── JSON output prompt builder ─────────────────────────────────────────────────
def build_json_prompt(table_desc: str, json_schema_str: str) -> tuple:
    """Build (system, user) for structured JSON output."""
    system = (
        "You are a data documentation specialist.\n"
        "CRITICAL: Return ONLY valid JSON. No markdown fences, no explanation, no trailing text.\n"
        "The response must be parseable by Python's json.loads() with zero modification."
    )
    user = f"""Generate documentation following EXACTLY this JSON schema:
{json_schema_str}

Table information:
{table_desc}

Return ONLY the JSON object."""
    return system, user


# ── YAML output prompt builder ─────────────────────────────────────────────────
def build_yaml_prompt(pipeline_desc: str) -> tuple:
    """Build (system, user) for structured YAML output."""
    system = (
        "You are a data pipeline architect. "
        "Return ONLY valid YAML — no markdown fences, no explanation."
    )
    user = f"""Convert this pipeline description to an Airflow DAG configuration in YAML.

Description: {pipeline_desc}

Return ONLY the YAML."""
    return system, user


# ── Library markdown generator ─────────────────────────────────────────────────
def generate_library_md(prompts: dict) -> str:
    """Generate the DE Prompt Library markdown from a prompts dict."""
    lines = [
        "# Sigma DataTech — DE Prompt Library",
        "",
        "> **Day 2 Deliverable** — GenAI for Data Engineering Bootcamp  ",
        "> Sigmoid Bangalore · May 2026  ",
        "> Built with LangChain PromptTemplate + Claude API",
        "",
        "---",
        "",
        "## Overview",
        "",
        "Reusable prompt templates for common Data Engineering tasks.",
        "Each template uses LangChain `PromptTemplate` variable syntax (`{variable_name}`).",
        "",
        "| # | Template | Use Case |",
        "|---|----------|----------|",
    ]

    for i, (name, data) in enumerate(prompts.items(), 1):
        lines.append(f"| {i} | {data['icon']} {name} | {data['description']} |")

    lines += ["", "---", ""]

    for name, data in prompts.items():
        var_list = list(data["variables"].keys())
        lines += [
            f"## {data['icon']} {name}",
            "",
            f"**Purpose:** {data['description']}",
            "",
            "### Template",
            "```",
            data["template"],
            "```",
            "",
            "### Variables",
            "",
            "| Variable | Example value |",
            "|----------|---------------|",
        ]
        for var, example in data["variables"].items():
            ex_short = str(example).replace("\n", " ")[:100]
            lines.append(f"| `{{{var}}}` | `{ex_short}` |")

        lines += [
            "",
            "### LangChain Usage",
            "",
            "```python",
            "from langchain_core.prompts import PromptTemplate",
            "from langchain_anthropic import ChatAnthropic",
            "from langchain_core.output_parsers import StrOutputParser",
            "",
            f"template = PromptTemplate(",
            f"    input_variables={var_list},",
            f"    template=TEMPLATE,  # from above",
            f")",
            "",
            "chain = template | ChatAnthropic(model='claude-haiku-4-5-20251001') | StrOutputParser()",
            "",
            "result = chain.invoke({",
        ]
        for var, example in data["variables"].items():
            ex_short = str(example).replace("\n", " ")[:60]
            lines.append(f'    "{var}": "{ex_short}",')
        lines += ["})", "```", "", "---", ""]

    lines += [
        "## Usage Guidelines",
        "",
        "1. **Test with real data** before deploying to production pipelines",
        "2. **Pin the model version** — never use model aliases in production code",
        "3. **Log prompts and responses** — needed for debugging and auditing",
        "4. **Version-control this file** — prompts are code; treat them as such",
        "5. **Add retry logic** for all JSON/YAML structured-output prompts",
        "6. **Use Prompt Caching** (Anthropic) when passing large static schemas repeatedly",
        "",
        "---",
        "",
        "*Sigma DataTech AI Infrastructure Team*  ",
        "*GenAI for Data Engineering Bootcamp, Sigmoid Bangalore 2026*",
    ]
    return "\n".join(lines)


# ── Gemini via Google AI Studio (OpenAI-compatible endpoint) ──────────────────
def call_gemini(
    api_key: str,
    system: str,
    messages: list,
    model: str = "gemini-3-flash-preview",
    max_tokens: int = 1200,
) -> tuple:
    """
    Call Gemini via Google AI Studio's OpenAI-compatible endpoint.
    Key from: aistudio.google.com → Get API Key (free with student account)
    Requires: pip install openai
    Returns (text, usage) on success, (None, None) on error.
    """
    if not api_key:
        return None, None
    try:
        from openai import OpenAI
        from collections import namedtuple
        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        full_messages = [{"role": "system", "content": system}] + messages
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0.2,
            messages=full_messages,
        )
        text = resp.choices[0].message.content or ""
        Usage = namedtuple("Usage", ["input_tokens", "output_tokens"])
        usage = Usage(
            input_tokens=getattr(resp.usage,  "prompt_tokens",     0),
            output_tokens=getattr(resp.usage, "completion_tokens", 0),
        )
        return text, usage
    except Exception:
        return None, None


# ── Claude API caller ──────────────────────────────────────────────────────────
def call_claude(
    api_key: str,
    system: str,
    messages: list,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 1200,
) -> tuple:
    """
    Call Claude via Anthropic SDK.
    Returns (text, usage) on success, (None, None) on empty key or error.
    """
    if not api_key:
        return None, None
    try:
        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return resp.content[0].text, resp.usage
    except Exception as e:
        print(f"[call_claude] ERROR: {e}")
        return None, str(e)


# ── Ollama local caller ────────────────────────────────────────────────────────
def call_ollama(
    system: str,
    messages: list,
    model: str = "qwen2.5:7b",
    max_tokens: int = 1200,
) -> tuple:
    """
    Call a local Ollama model (no API key needed).
    Returns (text, None) on success, (None, None) on error.
    """
    ollama_messages = [{"role": "system", "content": system}] + messages
    payload = json.dumps({
        "model": model,
        "messages": ollama_messages,
        "stream": False,
        "options": {"num_predict": max_tokens},
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            return result.get("message", {}).get("content", ""), None
    except Exception:
        return None, None
