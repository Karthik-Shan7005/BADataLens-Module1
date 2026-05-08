import anthropic
import asyncio
import json
import os
import pandas as pd
from typing import Optional
from dotenv import load_dotenv
from services.stats_engine import get_frequency, get_trend, get_top_box, get_mean

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

TOOLS = [
    {
        "name": "get_frequency",
        "description": (
            "Get frequency/percentage breakdown of a survey question, optionally filtered and weighted. "
            "Use when the question asks about distribution, percentages, or how many/what % of people "
            "gave a particular response. For single-code questions this shows % per answer option. "
            "For multi-response questions it shows % who selected each option (can sum to >100%)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question_code": {
                    "type": "string",
                    "description": "The question_id from the Question Registry",
                },
                "filters": {
                    "type": "object",
                    "description": (
                        "Optional filters as {question_id_or_variable: values}. "
                        "Values can be a list of codes (equality) or [min, max] for numeric ranges. "
                        "Example: {\"Q_AGE\": [25, 35], \"Q_USAGE\": [3]} means age 25-35 AND usage=3."
                    ),
                },
                "weighted": {
                    "type": "boolean",
                    "description": "Apply rim weights. Defaults to true when a weight variable exists.",
                },
                "wave": {
                    "type": "string",
                    "description": "Optional: filter to a specific wave value (e.g. '1', 'Wave 1 2024').",
                },
            },
            "required": ["question_code"],
        },
    },
    {
        "name": "get_trend",
        "description": (
            "Get wave-over-wave trend data for a question. Use when the question asks about "
            "changes over time, trends, or wave-by-wave comparisons. Returns the metric computed "
            "for each wave in the dataset."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question_code": {"type": "string"},
                "filters": {
                    "type": "object",
                    "description": "Optional demographic or behavioural filters.",
                },
                "weighted": {"type": "boolean"},
            },
            "required": ["question_code"],
        },
    },
    {
        "name": "get_top_box",
        "description": (
            "Get a box score for any values on a single-code scale question — supports both top and bottom box. "
            "Use top_values=[4,5] and box_label='Top 2 Box' for top box on a 5-point scale. "
            "Use top_values=[1,2] and box_label='Bottom 2 Box' for bottom box. "
            "Use top_values=[9,10] and box_label='NPS Promoters' for NPS. "
            "For multi-question summaries, call this tool once per question and compile results into a comparison table."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question_code": {"type": "string"},
                "top_values": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": (
                        "The numeric coded values that constitute the box score. "
                        "E.g. [4, 5] for top 2 box on a 5-point scale, [1, 2] for bottom 2 box, [9, 10] for NPS promoters."
                    ),
                },
                "box_label": {
                    "type": "string",
                    "description": "Label for this box score, e.g. 'Top 2 Box', 'Bottom 2 Box', 'Top 3 Box'. Defaults to 'Top Box'.",
                },
                "filters": {"type": "object"},
                "weighted": {"type": "boolean"},
                "wave": {"type": "string"},
            },
            "required": ["question_code", "top_values"],
        },
    },
    {
        "name": "get_mean",
        "description": (
            "Get the mean (average) score for a numeric or rating question. "
            "Use when the user asks for average score, mean rating, or average value."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question_code": {"type": "string"},
                "filters": {"type": "object"},
                "weighted": {"type": "boolean"},
                "wave": {"type": "string"},
            },
            "required": ["question_code"],
        },
    },
]


def _build_system_prompt(registry: dict, weight_variable: Optional[str], wave_variable: Optional[str]) -> str:
    registry_summary = json.dumps(
        {
            k: {
                "label": v["label"],
                "type": v["type"],
                "variables": v["variables"],
                "options": v["option_labels"] if v["option_labels"] else {},
            }
            for k, v in registry.items()
        },
        indent=2,
    )
    return f"""You are a market research data analyst. You help researchers and clients get insights from survey data by querying the dataset using the available tools.

Dataset configuration:
- Weight variable: {weight_variable or "None — unweighted study"}
- Wave variable: {wave_variable or "None — single wave study"}

Question Registry (all available questions and their variables):
{registry_summary}

Rules:
1. Always use the tools to fetch actual data before answering — never guess numbers.
2. Apply weights (weighted=true) whenever a weight variable exists.
3. Base = respondents satisfying the filter conditions, NOT the total sample.
4. Always state the base explicitly: e.g. "Base: 142 respondents aged 25–35 who used Brand X in the last 3 months (weighted)."
5. For multi-response questions, mention that % may sum to more than 100%.
6. Choose the right tool: get_frequency for distributions, get_trend for wave comparisons, get_top_box for positive score summaries, get_mean for averages.
7. Recommend an appropriate chart type at the end of your response: bar chart (distributions), line chart (trends), or pie chart (simple proportions).
8. Dual base: Every response must report total_n (all respondents satisfying the filter) and answered_n (those who actually answered this question). When they differ, the question was routed — lead with % of answered respondents (n=answered_n), then note the total base (N=total_n). When equal, report one base only.
9. Box scores: The options dict for each question maps SPSS numeric code → label (e.g. {"1": "Strongly Disagree", "5": "Strongly Agree"}). Use the numeric codes as top_values when calling get_top_box — never guess. Use the box_label from the tool result as your response heading. For multi-question comparisons, call get_top_box once per question and compile into a comparison table.
10. Be concise: lead with the key insight, then the supporting numbers."""


async def run_query(
    question: str,
    df: pd.DataFrame,
    registry: dict,
    weight_variable: Optional[str],
    wave_variable: Optional[str],
) -> dict:
    """
    Orchestrate a Claude tool-use loop to answer a natural language survey question.
    Returns {"response": str, "chart": dict | None}
    """
    system = _build_system_prompt(registry, weight_variable, wave_variable)
    messages = [{"role": "user", "content": question}]
    chart_data = None

    while True:
        response = await asyncio.to_thread(
            client.messages.create,
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = _execute_tool(
                        block.name, block.input, df, registry, weight_variable, wave_variable
                    )
                    if chart_data is None:
                        chart_data = _build_chart_data(block.name, result)

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        }
                    )

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            text = next((b.text for b in response.content if hasattr(b, "text")), "")
            return {"response": text, "chart": chart_data}


def _execute_tool(
    name: str,
    inputs: dict,
    df: pd.DataFrame,
    registry: dict,
    weight_variable: Optional[str],
    wave_variable: Optional[str],
) -> dict:
    inputs.setdefault("weighted", True)
    common = dict(df=df, registry=registry, weight_variable=weight_variable)

    if name == "get_frequency":
        return get_frequency(**common, wave_variable=wave_variable, **inputs)
    elif name == "get_trend":
        return get_trend(**common, wave_variable=wave_variable, **inputs)
    elif name == "get_top_box":
        return get_top_box(**common, wave_variable=wave_variable, **inputs)
    elif name == "get_mean":
        return get_mean(**common, wave_variable=wave_variable, **inputs)
    return {"error": f"Unknown tool: {name}"}


def _build_chart_data(tool_name: str, result: dict) -> Optional[dict]:
    if tool_name == "get_frequency" and "results" in result:
        entries = list(result["results"].values())
        total_n = result.get("total_n", result["base_n"])
        answered_n = result.get("answered_n", result["base_n"])
        base_label = (
            f"Total: N={total_n} | Answered: n={answered_n}"
            if total_n != answered_n
            else f"Base: N={total_n}{' (weighted)' if result.get('weighted') else ''}"
        )
        return {
            "type": "bar",
            "question_label": result.get("question_label", ""),
            "base_label": base_label,
            "labels": [e["label"] for e in entries],
            "datasets": [{"label": "% Respondents", "data": [e["pct"] for e in entries]}],
        }

    elif tool_name == "get_trend" and "trend" in result:
        waves = [t["wave"] for t in result["trend"]]
        # Build one dataset per answer option using the first wave's results as reference
        datasets = []
        if result["trend"]:
            first = result["trend"][0]["data"].get("results", {})
            for key, val in first.items():
                option_label = val.get("label", key)
                data_points = []
                for wave_entry in result["trend"]:
                    wave_results = wave_entry["data"].get("results", {})
                    data_points.append(wave_results.get(key, {}).get("pct", 0))
                datasets.append({"label": option_label, "data": data_points})
        return {
            "type": "line",
            "question_label": result.get("question_code", ""),
            "labels": waves,
            "datasets": datasets,
        }

    elif tool_name == "get_top_box":
        total_n = result.get("total_n", result.get("base_n"))
        answered_n = result.get("answered_n", result.get("base_n"))
        base_label = (
            f"Total: N={total_n} | Answered: n={answered_n}"
            if total_n != answered_n
            else f"Base: N={answered_n}"
        )
        box_label = result.get("box_label", f"Top box ({result.get('top_values')})")
        return {
            "type": "bar",
            "question_label": result.get("question_label", ""),
            "base_label": base_label,
            "labels": [box_label],
            "datasets": [{"label": box_label, "data": [result.get("pct", 0)]}],
        }

    elif tool_name == "get_mean":
        total_n = result.get("total_n", result.get("base_n"))
        answered_n = result.get("answered_n", result.get("base_n"))
        base_label = (
            f"Total: N={total_n} | Answered: n={answered_n}"
            if total_n != answered_n
            else f"Base: N={answered_n}"
        )
        return {
            "type": "bar",
            "question_label": result.get("question_label", ""),
            "base_label": base_label,
            "labels": ["Mean Score"],
            "datasets": [{"label": "Mean", "data": [result.get("mean", 0)]}],
        }

    return None
