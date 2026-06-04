"""
Static data: ROLES, DE_PROMPTS, DEFAULT_SCHEMA
Imported by helpers.py and app.py — no Streamlit dependency.
"""

DEFAULT_SCHEMA = """-- Sigma DataTech schema
CREATE TABLE sigma.customers (
    customer_id  BIGINT PRIMARY KEY,
    name         VARCHAR(200),
    email        VARCHAR(200),
    tier         VARCHAR(20),       -- 'bronze' | 'silver' | 'gold' | 'platinum'
    created_at   TIMESTAMP,
    country      VARCHAR(100)
);

CREATE TABLE sigma.orders (
    order_id     BIGINT PRIMARY KEY,
    customer_id  BIGINT REFERENCES sigma.customers,
    status       VARCHAR(20),       -- 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled'
    amount       DECIMAL(10,2),
    created_at   TIMESTAMP,
    delivered_at TIMESTAMP
);

CREATE TABLE sigma.order_items (
    item_id      BIGINT PRIMARY KEY,
    order_id     BIGINT REFERENCES sigma.orders,
    product_id   BIGINT,
    quantity     INTEGER,
    unit_price   DECIMAL(10,2)
);"""


ROLES = {
    "Senior Data Engineer (dbt + Airflow expert)":
        "You are a Senior Data Engineer with 10 years of experience, deep expertise in dbt "
        "and Apache Airflow, and strong opinionated views on pipeline design. Be direct, "
        "practical, and opinionated. Do not hedge.",

    "Cloud Architect (cost-optimisation focus)":
        "You are an AWS-certified Cloud Architect obsessed with cost optimisation and "
        "reliability. Always quantify cost implications and recommend right-sizing opportunities.",

    "Data Quality Engineer (testing advocate)":
        "You are a Data Quality Engineer who believes every untested pipeline is a liability. "
        "Always recommend validation layers, data contracts, and Great Expectations patterns.",

    "Sceptical Tech Lead (challenges assumptions)":
        "You are a sceptical Tech Lead who challenges every architectural decision. Ask hard "
        "questions, surface risks, and push back on assumptions before recommending anything.",

    "Junior Developer Explainer (plain language)":
        "You explain technical concepts in plain language for a non-technical audience. "
        "Use analogies, avoid jargon, and define every technical term you use.",

    "Junior Data Engineer (learning the basics, asks clarifying questions)":
        "You are a Junior Data Engineer still learning the basics of data pipelines, SQL, "
        "and cloud tools. You ask clarifying questions, show your reasoning step by step, "
        "and clearly flag when you are unsure about something.",
}


DE_PROMPTS = {
    "1. SQL Generation": {
        "icon": "🔍",
        "description": "Generate production-ready SQL from a natural language request",
        "template": """You are a {dialect} SQL expert at Sigma DataTech.
Write a production-ready query that: {nl_request}

Schema:
{schema}

Standards:
- Schema prefix: {db_schema}.
- Alias all columns with AS keyword
- Add inline comments for non-obvious business logic
- Use CTEs if more than 2 joins

Return ONLY the SQL inside a markdown code block.""",
        "variables": {
            "dialect":    "Snowflake",
            "nl_request": "Find platinum customers who have not ordered in the last 90 days",
            "schema":     "customers(id,name,tier,email), orders(id,customer_id,status,amount,created_at)",
            "db_schema":  "sigma",
        },
    },

    "2. Schema Documentation": {
        "icon": "📄",
        "description": "Auto-generate table documentation as structured JSON",
        "template": """You are a data documentation specialist at Sigma DataTech.
Generate documentation for this table and return as JSON.

Table DDL:
{ddl}

Business context:
{business_context}

Return JSON with these fields:
table_name, description, business_purpose, columns (array of name/type/description/nullable/pii),
tags (array), refresh_frequency, owner_team.

Return ONLY the JSON — no markdown fences, no explanation.""",
        "variables": {
            "ddl": (
                "CREATE TABLE sigma.orders ("
                "order_id BIGINT, customer_id BIGINT, status VARCHAR, "
                "amount DECIMAL, created_at TIMESTAMP, delivered_at TIMESTAMP)"
            ),
            "business_context": (
                "Central fact table for all customer orders. "
                "Source: Stripe webhooks via Kinesis Firehose."
            ),
        },
    },

    "3. Error Explanation": {
        "icon": "🔴",
        "description": "Explain and fix pipeline errors — plain English root cause + ordered fix steps",
        "template": """You are a senior Data Engineer at Sigma DataTech specialising in pipeline debugging.

Pipeline type: {pipeline_type}

Error:
{error_message}

Context:
{pipeline_context}

Provide:
1. **Root cause** — 1-2 sentences, plain English
2. **Why it happened** — technical explanation
3. **Fix** — exact steps, copy-paste commands where possible
4. **Prevention** — how to avoid recurrence

Be specific and actionable. No generic advice.""",
        "variables": {
            "pipeline_type":    "AWS Glue ETL job",
            "error_message":    "Job run exceeded the allocated execution time of 30 minutes and was terminated",
            "pipeline_context": (
                "Glue job reading 500 GB Parquet from S3, transforming with PySpark, "
                "writing to Redshift Serverless. Runs daily at 2 AM."
            ),
        },
    },

    "4. Data Quality Rules": {
        "icon": "✅",
        "description": "Generate Great Expectations-style data quality rules as a JSON array",
        "template": """You are a Data Quality Engineer at Sigma DataTech.
Generate validation rules for this column.

Table: {table_name}
Column: {column_name}
Data type: {data_type}
Business description: {business_description}
Sample values: {sample_values}

Return a JSON array where each element has these fields:
rule_name, expectation_type (Great Expectations format), description, parameters (object), severity (critical/warning/info).

Include rules covering: nullability, value ranges, format validation, referential integrity where applicable.
Return ONLY the JSON array — no markdown, no explanation.""",
        "variables": {
            "table_name":          "sigma.orders",
            "column_name":         "amount",
            "data_type":           "DECIMAL(10,2)",
            "business_description": "Order total in USD. Must be positive. Typical range $5-$50,000.",
            "sample_values":       "125.50, 89.99, 2500.00, 15.00",
        },
    },

    "5. Pipeline Description": {
        "icon": "🔁",
        "description": "Generate structured Markdown documentation from pipeline code or config",
        "template": """You are a technical writer for Sigma DataTech's data platform team.
Analyse this pipeline and generate structured documentation.

Pipeline code / config:
{pipeline_code}

Generate documentation with these sections:
1. **Overview** — 2 sentences: what it does and why
2. **Data Flow** — source to transformations to destination, step by step
3. **Schedule and Trigger**
4. **Dependencies** — upstream and downstream
5. **Key Business Logic** — important transformations in plain English
6. **Failure Handling**
7. **Owner and SLA**

Format as clean Markdown. Be specific — no generic boilerplate.""",
        "variables": {
            "pipeline_code": (
                "@dag(schedule='0 6 * * *', catchup=False)\n"
                "def orders_etl():\n"
                "    extract   = GlueJobOperator(job_name='sigma-extract-orders', s3_path='s3://sigma-raw/orders/')\n"
                "    transform = SparkSubmitOperator(app='transform_orders.py', args=['--dedup', '--validate'])\n"
                "    load      = S3ToRedshiftOperator(table='sigma_dw.fact_orders', mode='upsert', key='order_id')\n"
                "    extract >> transform >> load"
            ),
        },
    },

    "6. dbt Model Stub": {
        "icon": "🏗️",
        "description": "Generate a complete dbt model with SQL, schema YAML, and README stub",
        "template": """You are a senior dbt developer at Sigma DataTech.
Generate a complete dbt model stub for this requirement.

Model name: {model_name}
Layer: {layer}   (staging | intermediate | mart)
Business requirement: {requirement}
Source tables: {source_tables}

Generate three artefacts, clearly labelled:

1. **{model_name}.sql** — complete dbt model with:
   - Correct ref() and source() macros
   - Business logic comments
   - CTEs for readability

2. **schema.yml** — with:
   - Model description
   - Column descriptions
   - dbt tests: not_null, unique, accepted_values, relationships where applicable

3. **README section** — 3-bullet summary of what this model does and how to use it""",
        "variables": {
            "model_name":    "fct_customer_lifetime_value",
            "layer":         "mart",
            "requirement":   "Calculate lifetime value, order frequency, and churn risk score for each customer",
            "source_tables": "stg_orders, stg_customers, int_customer_orders",
        },
    },
}
