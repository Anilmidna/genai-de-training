"""
Phase 3 — Unit Tests: Day 2 Prompt Engineering Lab
TDD: tests written BEFORE implementation.

These tests define the expected contract for:
  helpers.py  — pure functions, zero Streamlit dependency
  prompts.py  — static data (ROLES, DE_PROMPTS, DEFAULT_SCHEMA)

Run:  pytest tests/ -v
      pytest tests/ -v --tb=short   (compact tracebacks)
"""

import json
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Allow imports from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers import (
    estimate_tokens,
    fill_template,
    parse_json_response,
    build_shot_prompt,
    build_cot_prompt,
    build_react_prompt,
    build_role_prompt,
    build_nl_sql_prompt,
    build_sql_nl_prompt,
    build_json_prompt,
    build_yaml_prompt,
    generate_library_md,
    call_claude,
)
from prompts import DE_PROMPTS, ROLES, DEFAULT_SCHEMA


# ══════════════════════════════════════════════════════════════════════════════
#  1. TOKEN ESTIMATOR
# ══════════════════════════════════════════════════════════════════════════════
class TestEstimateTokens:

    def test_empty_string_returns_zero(self):
        assert estimate_tokens("") == 0

    def test_four_chars_equals_one_token(self):
        assert estimate_tokens("abcd") == 1

    def test_estimate_is_chars_divided_by_four(self):
        text = "a" * 400
        assert estimate_tokens(text) == 100

    def test_typical_sql_line_within_expected_range(self):
        sql = "SELECT customer_id, SUM(amount) AS total FROM sigma.orders GROUP BY 1;"
        tokens = estimate_tokens(sql)
        assert 10 <= tokens <= 25

    def test_large_schema_within_expected_range(self):
        schema = DEFAULT_SCHEMA
        tokens = estimate_tokens(schema)
        # A realistic schema should be between 100 and 2000 tokens
        assert 100 <= tokens <= 2000

    def test_returns_integer(self):
        assert isinstance(estimate_tokens("hello world"), int)


# ══════════════════════════════════════════════════════════════════════════════
#  2. TEMPLATE FILLER
# ══════════════════════════════════════════════════════════════════════════════
class TestFillTemplate:

    def test_single_variable_substituted(self):
        result = fill_template("Hello {name}", {"name": "Sigma"})
        assert result == "Hello Sigma"

    def test_multiple_variables_substituted(self):
        result = fill_template("Table: {table} | Dialect: {dialect}", {
            "table": "orders",
            "dialect": "Snowflake",
        })
        assert result == "Table: orders | Dialect: Snowflake"

    def test_template_with_no_variables_unchanged(self):
        tmpl = "No variables here."
        assert fill_template(tmpl, {}) == tmpl

    def test_extra_variables_in_dict_are_ignored(self):
        result = fill_template("Hello {name}", {"name": "Sigma", "extra": "ignored"})
        assert result == "Hello Sigma"

    def test_missing_variable_leaves_placeholder_intact(self):
        result = fill_template("Hello {name} from {city}", {"name": "Sigma"})
        assert "{city}" in result

    def test_multiline_template_works(self):
        tmpl = "Role: {role}\nTable: {table}"
        result = fill_template(tmpl, {"role": "DE", "table": "orders"})
        assert "Role: DE" in result
        assert "Table: orders" in result

    def test_returns_string(self):
        assert isinstance(fill_template("{x}", {"x": "y"}), str)


# ══════════════════════════════════════════════════════════════════════════════
#  3. JSON RESPONSE PARSER
# ══════════════════════════════════════════════════════════════════════════════
class TestParseJsonResponse:
    """
    parse_json_response(text) -> (parsed: dict|list|None, is_valid: bool, error: str)
    """

    def test_valid_json_object_returns_parsed(self):
        text = '{"table_name": "orders", "owner": "sigma"}'
        parsed, is_valid, error = parse_json_response(text)
        assert is_valid is True
        assert parsed["table_name"] == "orders"
        assert error == ""

    def test_valid_json_array_returns_parsed(self):
        text = '[{"rule": "not_null"}, {"rule": "unique"}]'
        parsed, is_valid, error = parse_json_response(text)
        assert is_valid is True
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_invalid_json_returns_false_and_error(self):
        text = "This is not JSON at all."
        parsed, is_valid, error = parse_json_response(text)
        assert is_valid is False
        assert parsed is None
        assert len(error) > 0

    def test_empty_string_returns_false(self):
        parsed, is_valid, error = parse_json_response("")
        assert is_valid is False
        assert parsed is None

    def test_json_wrapped_in_markdown_fences_is_parsed(self):
        text = "```json\n{\"key\": \"value\"}\n```"
        parsed, is_valid, error = parse_json_response(text)
        assert is_valid is True
        assert parsed["key"] == "value"

    def test_truncated_json_returns_false(self):
        text = '{"table_name": "orders"'  # missing closing brace
        parsed, is_valid, error = parse_json_response(text)
        assert is_valid is False

    def test_error_message_is_string(self):
        _, _, error = parse_json_response("bad json")
        assert isinstance(error, str)


# ══════════════════════════════════════════════════════════════════════════════
#  4. SHOT PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════
class TestBuildShotPrompt:
    """
    build_shot_prompt(task, shot_type) -> (system: str, user: str)
    shot_type: "Zero-shot" | "One-shot" | "Few-shot"
    """

    def test_returns_tuple_of_two_strings(self):
        system, user = build_shot_prompt("Find top 5 customers", "Zero-shot")
        assert isinstance(system, str)
        assert isinstance(user, str)

    def test_zero_shot_user_contains_task(self):
        task = "Find top 5 customers by revenue"
        _, user = build_shot_prompt(task, "Zero-shot")
        assert task in user

    def test_zero_shot_user_has_no_examples(self):
        _, user = build_shot_prompt("Find top 5 customers", "Zero-shot")
        assert "EXAMPLE" not in user.upper()

    def test_one_shot_user_contains_one_example(self):
        _, user = build_shot_prompt("Find top 5 customers", "One-shot")
        assert "EXAMPLE" in user.upper() or "example" in user.lower()

    def test_few_shot_user_contains_multiple_examples(self):
        _, user = build_shot_prompt("Find top 5 customers", "Few-shot")
        assert user.upper().count("EXAMPLE") >= 2

    def test_few_shot_user_contains_task(self):
        task = "Find customers with 3+ orders"
        _, user = build_shot_prompt(task, "Few-shot")
        assert task in user

    def test_system_is_non_empty_for_all_types(self):
        for shot_type in ["Zero-shot", "One-shot", "Few-shot"]:
            system, _ = build_shot_prompt("task", shot_type)
            assert len(system) > 0

    def test_invalid_shot_type_raises_value_error(self):
        with pytest.raises(ValueError):
            build_shot_prompt("task", "Ten-shot")


# ══════════════════════════════════════════════════════════════════════════════
#  5. CHAIN-OF-THOUGHT PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════
class TestBuildCotPrompt:
    """
    build_cot_prompt(problem, use_cot) -> (system: str, user: str)
    """

    def test_returns_tuple_of_two_strings(self):
        system, user = build_cot_prompt("Glue OOM error", True)
        assert isinstance(system, str) and isinstance(user, str)

    def test_cot_enabled_user_contains_step_by_step_instruction(self):
        _, user = build_cot_prompt("Glue OOM error", True)
        assert "step" in user.lower()

    def test_cot_disabled_user_equals_problem_only(self):
        problem = "Glue OOM error on 50 GB CSV"
        _, user = build_cot_prompt(problem, False)
        assert user.strip() == problem.strip()

    def test_cot_enabled_user_contains_problem(self):
        problem = "PySpark 4x slower after upgrade"
        _, user = build_cot_prompt(problem, True)
        assert problem in user

    def test_system_references_data_engineering(self):
        system, _ = build_cot_prompt("any problem", True)
        assert any(kw in system.lower() for kw in ["data engineer", "spark", "pipeline"])


# ══════════════════════════════════════════════════════════════════════════════
#  6. REACT PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════
class TestBuildReactPrompt:
    """
    build_react_prompt(scenario) -> (system: str, user: str)
    """

    def test_returns_tuple_of_two_strings(self):
        system, user = build_react_prompt("Airflow DAG failing")
        assert isinstance(system, str) and isinstance(user, str)

    def test_system_contains_react_format_keywords(self):
        system, _ = build_react_prompt("Airflow DAG failing")
        system_lower = system.lower()
        assert "thought" in system_lower
        assert "action" in system_lower
        assert "observation" in system_lower

    def test_user_contains_scenario(self):
        scenario = "Snowflake query 10x slower than baseline"
        _, user = build_react_prompt(scenario)
        assert scenario in user

    def test_system_instructs_final_answer(self):
        system, _ = build_react_prompt("any scenario")
        assert "final answer" in system.lower()


# ══════════════════════════════════════════════════════════════════════════════
#  7. ROLE PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════
class TestBuildRolePrompt:
    """
    build_role_prompt(role_name, question) -> (system: str, user: str)
    role_name must be a key in ROLES dict
    """

    def test_returns_tuple_of_two_strings(self):
        role = list(ROLES.keys())[0]
        system, user = build_role_prompt(role, "Should we use Airflow or Prefect?")
        assert isinstance(system, str) and isinstance(user, str)

    def test_system_contains_role_description(self):
        role = list(ROLES.keys())[0]
        system, _ = build_role_prompt(role, "any question")
        assert ROLES[role][:30] in system

    def test_user_contains_question(self):
        question = "Should we use Lambda or Kappa architecture?"
        role = list(ROLES.keys())[0]
        _, user = build_role_prompt(role, question)
        assert question in user

    def test_invalid_role_raises_key_error(self):
        with pytest.raises(KeyError):
            build_role_prompt("Non-existent Role", "question")

    def test_all_six_roles_are_valid(self):
        question = "Should we migrate to Prefect?"
        for role_name in ROLES:
            system, user = build_role_prompt(role_name, question)
            assert len(system) > 0
            assert question in user


# ══════════════════════════════════════════════════════════════════════════════
#  8. NL → SQL PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════
class TestBuildNlSqlPrompt:
    """
    build_nl_sql_prompt(schema, question, dialect) -> (system: str, user: str)
    """

    def test_returns_tuple_of_two_strings(self):
        system, user = build_nl_sql_prompt(DEFAULT_SCHEMA, "Top 5 customers", "Snowflake")
        assert isinstance(system, str) and isinstance(user, str)

    def test_system_contains_dialect(self):
        system, _ = build_nl_sql_prompt(DEFAULT_SCHEMA, "Top 5 customers", "BigQuery")
        assert "BigQuery" in system

    def test_user_contains_schema(self):
        _, user = build_nl_sql_prompt(DEFAULT_SCHEMA, "Top 5 customers", "Snowflake")
        assert "sigma.customers" in user or "sigma.orders" in user

    def test_user_contains_question(self):
        question = "Find customers with more than 5 orders"
        _, user = build_nl_sql_prompt(DEFAULT_SCHEMA, question, "Snowflake")
        assert question in user

    def test_system_instructs_sql_code_block_output(self):
        system, _ = build_nl_sql_prompt(DEFAULT_SCHEMA, "any", "Snowflake")
        assert "sql" in system.lower() or "code block" in system.lower() or "markdown" in system.lower()

    def test_supported_dialects(self):
        for dialect in ["Snowflake", "PostgreSQL", "BigQuery", "Spark SQL"]:
            system, _ = build_nl_sql_prompt(DEFAULT_SCHEMA, "Top 5 customers", dialect)
            assert dialect in system


# ══════════════════════════════════════════════════════════════════════════════
#  9. SQL → NL PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════
class TestBuildSqlNlPrompt:
    """
    build_sql_nl_prompt(sql, audience) -> (system: str, user: str)
    """

    SAMPLE_SQL = "SELECT customer_id, SUM(amount) FROM sigma.orders GROUP BY 1;"

    def test_returns_tuple_of_two_strings(self):
        system, user = build_sql_nl_prompt(self.SAMPLE_SQL, "Business Analyst (no SQL knowledge)")
        assert isinstance(system, str) and isinstance(user, str)

    def test_user_contains_sql(self):
        _, user = build_sql_nl_prompt(self.SAMPLE_SQL, "Business Analyst (no SQL knowledge)")
        assert "SELECT" in user or "customer_id" in user

    def test_user_contains_audience_instruction(self):
        _, user = build_sql_nl_prompt(self.SAMPLE_SQL, "Business Analyst (no SQL knowledge)")
        assert "business" in user.lower() or "plain" in user.lower() or "analyst" in user.lower()

    def test_all_four_audiences_produce_non_empty_prompts(self):
        audiences = [
            "Business Analyst (no SQL knowledge)",
            "Junior Developer (knows basic SQL)",
            "Product Manager (needs the business so-what)",
            "Data Architect (full technical + performance detail)",
        ]
        for audience in audiences:
            system, user = build_sql_nl_prompt(self.SAMPLE_SQL, audience)
            assert len(system) > 0 and len(user) > 0


# ══════════════════════════════════════════════════════════════════════════════
#  10. JSON OUTPUT PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════
class TestBuildJsonPrompt:
    """
    build_json_prompt(table_desc, json_schema_str) -> (system: str, user: str)
    """

    TABLE_DESC = "Table: sigma.orders\nColumns: order_id, customer_id, status, amount"
    JSON_SCHEMA = '{"table_name": "string", "description": "string"}'

    def test_returns_tuple_of_two_strings(self):
        system, user = build_json_prompt(self.TABLE_DESC, self.JSON_SCHEMA)
        assert isinstance(system, str) and isinstance(user, str)

    def test_system_instructs_json_only_output(self):
        system, _ = build_json_prompt(self.TABLE_DESC, self.JSON_SCHEMA)
        assert "json" in system.lower()
        assert any(kw in system.lower() for kw in ["only", "no markdown", "no explanation"])

    def test_user_contains_table_description(self):
        _, user = build_json_prompt(self.TABLE_DESC, self.JSON_SCHEMA)
        assert "sigma.orders" in user

    def test_user_contains_schema(self):
        _, user = build_json_prompt(self.TABLE_DESC, self.JSON_SCHEMA)
        assert "table_name" in user


# ══════════════════════════════════════════════════════════════════════════════
#  11. YAML OUTPUT PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════
class TestBuildYamlPrompt:
    """
    build_yaml_prompt(pipeline_desc) -> (system: str, user: str)
    """

    PIPE_DESC = "Daily Airflow DAG at 6 AM reading from S3, transforming with Glue, loading to Redshift."

    def test_returns_tuple_of_two_strings(self):
        system, user = build_yaml_prompt(self.PIPE_DESC)
        assert isinstance(system, str) and isinstance(user, str)

    def test_system_instructs_yaml_only(self):
        system, _ = build_yaml_prompt(self.PIPE_DESC)
        assert "yaml" in system.lower()
        assert any(kw in system.lower() for kw in ["only", "no markdown", "no explanation"])

    def test_user_contains_pipeline_description(self):
        _, user = build_yaml_prompt(self.PIPE_DESC)
        assert self.PIPE_DESC in user


# ══════════════════════════════════════════════════════════════════════════════
#  12. LIBRARY MARKDOWN GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
class TestGenerateLibraryMd:

    def test_returns_non_empty_string(self):
        result = generate_library_md(DE_PROMPTS)
        assert isinstance(result, str) and len(result) > 0

    def test_contains_all_six_prompt_names(self):
        result = generate_library_md(DE_PROMPTS)
        for name in DE_PROMPTS:
            assert name in result, f"Prompt '{name}' not found in generated markdown"

    def test_contains_markdown_table_of_contents(self):
        result = generate_library_md(DE_PROMPTS)
        assert "|" in result  # markdown table uses pipes

    def test_contains_langchain_usage_section(self):
        result = generate_library_md(DE_PROMPTS)
        assert "PromptTemplate" in result
        assert "ChatAnthropic" in result

    def test_contains_usage_guidelines_section(self):
        result = generate_library_md(DE_PROMPTS)
        assert "Usage Guidelines" in result or "usage" in result.lower()

    def test_contains_sigma_datatech_branding(self):
        result = generate_library_md(DE_PROMPTS)
        assert "Sigma DataTech" in result

    def test_custom_prompts_dict_reflected_in_output(self):
        custom = {
            "Test Prompt": {
                "icon": "🧪",
                "description": "A test prompt",
                "template": "Do {task}",
                "variables": {"task": "something"},
            }
        }
        result = generate_library_md(custom)
        assert "Test Prompt" in result
        assert "A test prompt" in result


# ══════════════════════════════════════════════════════════════════════════════
#  13. CALL CLAUDE (mocked)
# ══════════════════════════════════════════════════════════════════════════════
class TestCallClaude:
    """
    call_claude(api_key, system, messages, model, max_tokens)
      -> (text: str, usage: object) | (None, None)
    """

    MESSAGES = [{"role": "user", "content": "Hello"}]

    def test_empty_api_key_returns_none_none(self):
        text, usage = call_claude("", "system", self.MESSAGES)
        assert text is None and usage is None

    def test_none_api_key_returns_none_none(self):
        text, usage = call_claude(None, "system", self.MESSAGES)
        assert text is None and usage is None

    def test_valid_key_returns_text_and_usage(self):
        with patch("helpers.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_resp = MagicMock()
            mock_resp.content = [MagicMock(text="Generated SQL here")]
            mock_resp.usage = MagicMock(input_tokens=50, output_tokens=20)
            mock_client.messages.create.return_value = mock_resp

            text, usage = call_claude("sk-ant-test123", "You are a SQL expert", self.MESSAGES)

        assert text == "Generated SQL here"
        assert usage.input_tokens == 50
        assert usage.output_tokens == 20

    def test_api_exception_returns_none_none(self):
        with patch("helpers.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("Connection refused")

            text, usage = call_claude("sk-ant-test123", "system", self.MESSAGES)

        assert text is None and usage is None

    def test_correct_model_passed_to_api(self):
        with patch("helpers.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_resp = MagicMock()
            mock_resp.content = [MagicMock(text="ok")]
            mock_resp.usage = MagicMock(input_tokens=10, output_tokens=5)
            mock_client.messages.create.return_value = mock_resp

            call_claude("sk-ant-test", "sys", self.MESSAGES, model="claude-sonnet-4-6")
            call_args = mock_client.messages.create.call_args

        assert call_args.kwargs["model"] == "claude-sonnet-4-6"

    def test_max_tokens_passed_to_api(self):
        with patch("helpers.Anthropic") as MockAnthropic:
            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client
            mock_resp = MagicMock()
            mock_resp.content = [MagicMock(text="ok")]
            mock_resp.usage = MagicMock(input_tokens=10, output_tokens=5)
            mock_client.messages.create.return_value = mock_resp

            call_claude("sk-ant-test", "sys", self.MESSAGES, max_tokens=512)
            call_args = mock_client.messages.create.call_args

        assert call_args.kwargs["max_tokens"] == 512


# ══════════════════════════════════════════════════════════════════════════════
#  14. PROMPTS DATA INTEGRITY
# ══════════════════════════════════════════════════════════════════════════════
class TestDePromptsData:

    REQUIRED_KEYS = {"icon", "description", "template", "variables"}
    REQUIRED_PROMPTS = {
        "1. SQL Generation",
        "2. Schema Documentation",
        "3. Error Explanation",
        "4. Data Quality Rules",
        "5. Pipeline Description",
        "6. dbt Model Stub",
    }

    def test_exactly_six_prompts_exist(self):
        assert len(DE_PROMPTS) == 6

    def test_all_six_required_prompts_present(self):
        for name in self.REQUIRED_PROMPTS:
            assert name in DE_PROMPTS, f"Missing prompt: '{name}'"

    def test_each_prompt_has_required_keys(self):
        for name, data in DE_PROMPTS.items():
            for key in self.REQUIRED_KEYS:
                assert key in data, f"Prompt '{name}' missing key '{key}'"

    def test_all_templates_are_non_empty_strings(self):
        for name, data in DE_PROMPTS.items():
            assert isinstance(data["template"], str) and len(data["template"]) > 20, \
                f"Prompt '{name}' has empty or trivial template"

    def test_all_variables_dicts_are_non_empty(self):
        for name, data in DE_PROMPTS.items():
            assert isinstance(data["variables"], dict) and len(data["variables"]) > 0, \
                f"Prompt '{name}' has empty variables dict"

    def test_template_variables_match_variables_dict(self):
        import re
        for name, data in DE_PROMPTS.items():
            template_vars = set(re.findall(r'\{(\w+)\}', data["template"]))
            declared_vars = set(data["variables"].keys())
            missing = template_vars - declared_vars
            assert not missing, \
                f"Prompt '{name}' has template vars {missing} not in variables dict"

    def test_all_icons_are_non_empty(self):
        for name, data in DE_PROMPTS.items():
            assert len(data["icon"]) > 0, f"Prompt '{name}' has empty icon"


# ══════════════════════════════════════════════════════════════════════════════
#  15. ROLES DATA INTEGRITY
# ══════════════════════════════════════════════════════════════════════════════
class TestRolesData:

    REQUIRED_ROLES = {
        "Senior Data Engineer (dbt + Airflow expert)",
        "Cloud Architect (cost-optimisation focus)",
        "Data Quality Engineer (testing advocate)",
        "Sceptical Tech Lead (challenges assumptions)",
        "Junior Developer Explainer (plain language)",
        "Junior Data Engineer (learning the basics, asks clarifying questions)",
    }

    def test_exactly_six_roles_exist(self):
        assert len(ROLES) == 6

    def test_all_six_required_roles_present(self):
        for role in self.REQUIRED_ROLES:
            assert role in ROLES, f"Missing role: '{role}'"

    def test_all_role_descriptions_are_non_empty(self):
        for role, desc in ROLES.items():
            assert isinstance(desc, str) and len(desc) > 20, \
                f"Role '{role}' has empty or trivial description"

    def test_junior_data_engineer_role_description_is_appropriate(self):
        role = "Junior Data Engineer (learning the basics, asks clarifying questions)"
        desc = ROLES[role].lower()
        assert any(kw in desc for kw in ["junior", "learning", "basic", "clarif"]), \
            "Junior Data Engineer description does not reflect a learning persona"

    def test_senior_de_role_is_opinionated(self):
        role = "Senior Data Engineer (dbt + Airflow expert)"
        desc = ROLES[role].lower()
        assert any(kw in desc for kw in ["opinionated", "direct", "expert", "senior"])


# ══════════════════════════════════════════════════════════════════════════════
#  16. DEFAULT SCHEMA DATA
# ══════════════════════════════════════════════════════════════════════════════
class TestDefaultSchema:

    def test_schema_is_non_empty_string(self):
        assert isinstance(DEFAULT_SCHEMA, str) and len(DEFAULT_SCHEMA) > 0

    def test_schema_contains_sigma_prefix(self):
        assert "sigma." in DEFAULT_SCHEMA.lower() or "sigma" in DEFAULT_SCHEMA.lower()

    def test_schema_contains_customers_table(self):
        assert "customers" in DEFAULT_SCHEMA.lower()

    def test_schema_contains_orders_table(self):
        assert "orders" in DEFAULT_SCHEMA.lower()

    def test_schema_contains_at_least_one_column_definition(self):
        assert any(t in DEFAULT_SCHEMA.upper() for t in ["BIGINT", "VARCHAR", "TIMESTAMP", "DECIMAL"])
