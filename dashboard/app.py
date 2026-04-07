import json
import logging
from pathlib import Path
import sys

import altair as alt
import pandas as pd
import streamlit as st

# Ensure project-root imports work when Streamlit executes this file directly.
if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (
    COL_STOCK_CODE,
    DASHBOARD_PRIMARY_METRICS,
    EVALUATION_PRODUCT_METRIC_LEVEL,
    EVALUATION_STATISTICAL_TESTS_PATH,
    EVALUATION_STRATEGY_METRICS_PATH,
    EVALUATION_STRATEGY_SUMMARY_PATH,
    DASHBOARD_PRODUCT_COMPARISON_METRICS,
    DASHBOARD_PRODUCT_METRIC_COLUMNS,
    DASHBOARD_SECTION_TITLES,
    DASHBOARD_SIGNIFICANCE_THRESHOLD,
    DASHBOARD_STABILITY_SUPPORTING_METRICS,
    DASHBOARD_STATISTICAL_TEST_LABELS,
    DASHBOARD_SUPPORTING_METRICS,
    DASHBOARD_SUMMARY_METRICS,
    DASHBOARD_TEST_LABELS,
    PROJECT_ROOT,
    SIMULATION_STRATEGIES,
)
from pipeline.execution import DASHBOARD_COMMAND, command_logging_targets
from preprocessing.common import configured_path
from utils.data_contracts import validate_evaluation_metrics, validate_evaluation_summary, validate_evaluation_tests
from utils.logging_config import configure_logging

logger = logging.getLogger("dashboard.app")


def _format_metric_label(metric_name: str) -> str:
    return metric_name.replace("_", " ").title()


def _format_number(value: float) -> str:
    return f"{value:,.6f}" if abs(value) < 10 else f"{value:,.3f}"


def _evaluation_input_paths() -> dict[str, str]:
    return {
        "strategy_metrics": str(configured_path(PROJECT_ROOT, EVALUATION_STRATEGY_METRICS_PATH)),
        "strategy_summary": str(configured_path(PROJECT_ROOT, EVALUATION_STRATEGY_SUMMARY_PATH)),
        "statistical_tests": str(configured_path(PROJECT_ROOT, EVALUATION_STATISTICAL_TESTS_PATH)),
    }


def _ensure_file_exists(path_label: str, path_value: str) -> None:
    path = configured_path(PROJECT_ROOT, path_value)
    if not path.exists():
        raise FileNotFoundError(f"Missing required Evaluation artifact: {path_label} -> {path}")


def _dashboard_product_metrics_view(metrics_df: pd.DataFrame) -> pd.DataFrame:
    product_metrics_df = metrics_df.loc[
        metrics_df["metric_level"] == EVALUATION_PRODUCT_METRIC_LEVEL,
        DASHBOARD_PRODUCT_METRIC_COLUMNS,
    ].copy()
    if product_metrics_df.empty:
        raise ValueError("strategy_metrics.parquet does not contain any product-level rows.")

    actual_strategies = set(product_metrics_df["strategy"].astype(str).unique().tolist())
    expected_strategies = set(SIMULATION_STRATEGIES)
    if actual_strategies != expected_strategies:
        raise ValueError(
            "Dashboard product-level metrics validation failed: strategy mismatch after product filtering.\n"
            f"Expected strategies: {sorted(expected_strategies)}\n"
            f"Actual strategies:   {sorted(actual_strategies)}"
        )

    product_metrics_df[COL_STOCK_CODE] = product_metrics_df[COL_STOCK_CODE].astype(str)
    product_metrics_df = product_metrics_df.sort_values([COL_STOCK_CODE, "strategy"], kind="mergesort").reset_index(drop=True)
    return product_metrics_df


@st.cache_data(show_spinner=False)
def load_dashboard_inputs() -> tuple[pd.DataFrame, dict[str, dict[str, float]], dict[str, dict[str, dict[str, dict[str, float]]]]]:
    _ensure_file_exists("strategy_metrics", EVALUATION_STRATEGY_METRICS_PATH)
    _ensure_file_exists("strategy_summary", EVALUATION_STRATEGY_SUMMARY_PATH)
    _ensure_file_exists("statistical_tests", EVALUATION_STATISTICAL_TESTS_PATH)

    metrics_df = pd.read_parquet(configured_path(PROJECT_ROOT, EVALUATION_STRATEGY_METRICS_PATH))
    summary_payload = json.loads(
        configured_path(PROJECT_ROOT, EVALUATION_STRATEGY_SUMMARY_PATH).read_text(encoding="utf-8")
    )
    statistical_payload = json.loads(
        configured_path(PROJECT_ROOT, EVALUATION_STATISTICAL_TESTS_PATH).read_text(encoding="utf-8")
    )

    validate_evaluation_metrics(metrics_df)
    validate_evaluation_summary(summary_payload)
    validate_evaluation_tests(statistical_payload)

    return (
        _dashboard_product_metrics_view(metrics_df),
        summary_payload,
        statistical_payload,
    )


def _summary_frame(summary_payload: dict[str, dict[str, float]]) -> pd.DataFrame:
    summary_df = pd.DataFrame.from_dict(summary_payload, orient="index")
    summary_df.index.name = "strategy"
    summary_df = summary_df.reset_index()
    return summary_df[["strategy", *DASHBOARD_SUMMARY_METRICS]]


def _strategy_for_metric(summary_df: pd.DataFrame, metric_name: str, *, ascending: bool) -> str:
    ranked_df = summary_df.sort_values(metric_name, ascending=ascending, kind="mergesort").reset_index(drop=True)
    return str(ranked_df.iloc[0]["strategy"])


def _metric_rankings(summary_df: pd.DataFrame, metric_name: str, *, ascending: bool) -> list[str]:
    ranked_df = summary_df.sort_values(metric_name, ascending=ascending, kind="mergesort").reset_index(drop=True)
    return ranked_df["strategy"].astype(str).tolist()


def _render_primary_findings(summary_df: pd.DataFrame) -> None:
    revenue_ranking = _metric_rankings(summary_df, "total_revenue", ascending=False)
    stability_ranking = _metric_rankings(summary_df, "mean_absolute_change", ascending=True)

    st.markdown(
        (
            f"Primary result: **{revenue_ranking[0].upper()}** delivers the highest total revenue, while "
            f"**{stability_ranking[0].upper()}** delivers the lowest mean absolute change under the shared simulation setting."
        )
    )
    st.caption(
        (
            f"This frames the core trade-off directly: revenue ranking is "
            f"{' > '.join(strategy.upper() for strategy in revenue_ranking)}, while stability ranking is "
            f"{' < '.join(strategy.upper() for strategy in stability_ranking)}."
        )
    )


def _render_kpi_summary(summary_df: pd.DataFrame) -> None:
    st.subheader(DASHBOARD_SECTION_TITLES["summary"])
    st.caption(
        "Primary metrics answer the research question directly. Supporting metrics remain available for interpretation only."
    )
    _render_primary_findings(summary_df)

    strategies = summary_df["strategy"].tolist()
    columns = st.columns(len(strategies))
    revenue_leader = _strategy_for_metric(summary_df, "total_revenue", ascending=False)
    stability_leader = _strategy_for_metric(summary_df, "mean_absolute_change", ascending=True)

    for column, strategy_name in zip(columns, strategies, strict=False):
        strategy_row = summary_df.loc[summary_df["strategy"] == strategy_name].iloc[0]
        with column:
            st.markdown(f"**{strategy_name.upper()}**")
            highlights: list[str] = []
            if strategy_name == revenue_leader:
                highlights.append("Highest revenue")
            if strategy_name == stability_leader:
                highlights.append("Lowest mean absolute change")
            if highlights:
                st.caption(" | ".join(highlights))
            else:
                st.caption("Supporting comparator")
            for metric_name in DASHBOARD_PRIMARY_METRICS:
                st.metric(_format_metric_label(metric_name), _format_number(float(strategy_row[metric_name])))

    st.markdown("**Supporting Metrics**")
    display_df = summary_df.copy()
    display_df = display_df[["strategy", *DASHBOARD_SUPPORTING_METRICS]]
    for metric_name in DASHBOARD_SUPPORTING_METRICS:
        display_df[metric_name] = display_df[metric_name].map(lambda value: round(float(value), 6))
    st.dataframe(display_df, width="stretch", hide_index=True)


def _bar_chart(dataframe: pd.DataFrame, metric_name: str, title: str) -> alt.Chart:
    return (
        alt.Chart(dataframe)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("strategy:N", title="Strategy", sort=dataframe["strategy"].tolist()),
            y=alt.Y(f"{metric_name}:Q", title=_format_metric_label(metric_name)),
            color=alt.Color("strategy:N", legend=None),
            tooltip=[
                alt.Tooltip("strategy:N", title="Strategy"),
                alt.Tooltip(f"{metric_name}:Q", title=_format_metric_label(metric_name), format=",.6f"),
            ],
        )
        .properties(height=320, title=title)
    )


def _render_revenue_comparison(summary_df: pd.DataFrame) -> None:
    st.subheader(DASHBOARD_SECTION_TITLES["revenue"])
    revenue_ranking = _metric_rankings(summary_df, "total_revenue", ascending=False)
    st.markdown(
        f"Interpretation: **{revenue_ranking[0].upper()}** achieves the highest total revenue under the shared simulated demand conditions."
    )
    st.caption(
        f"Mean daily revenue is shown as a secondary measure to support interpretation rather than drive the main conclusion."
    )

    left_column, right_column = st.columns([1.35, 1.0])
    with left_column:
        st.altair_chart(
            _bar_chart(summary_df, "total_revenue", "Total Revenue by Strategy"),
            width="stretch",
        )
    with right_column:
        st.altair_chart(
            _bar_chart(summary_df, "mean_daily_revenue", "Mean Daily Revenue by Strategy"),
            width="stretch",
        )


def _render_stability_comparison(summary_df: pd.DataFrame) -> None:
    st.subheader(DASHBOARD_SECTION_TITLES["stability"])
    stability_leader = _strategy_for_metric(summary_df, "mean_absolute_change", ascending=True)
    supporting_metric_leaders = {
        metric_name: _strategy_for_metric(summary_df, metric_name, ascending=True)
        for metric_name in DASHBOARD_STABILITY_SUPPORTING_METRICS
    }
    supporting_alignment = all(strategy_name == stability_leader for strategy_name in supporting_metric_leaders.values())
    if supporting_alignment:
        st.markdown(
            f"Interpretation: **{stability_leader.upper()}** demonstrates the lowest price volatility across the primary and supporting stability measures."
        )
    else:
        st.markdown(
            f"Interpretation: **{stability_leader.upper()}** delivers the lowest mean absolute change, with supporting stability metrics used to explain the broader behaviour."
        )
    st.caption(
        "Mean absolute change is the primary stability metric. The other three measures support interpretation rather than serve as headline results."
    )

    st.altair_chart(
        _bar_chart(summary_df, "mean_absolute_change", "Mean Absolute Change by Strategy"),
        width="stretch",
    )

    chart_columns = st.columns(3)
    stability_metrics = [
        ("price_std", "Price Standard Deviation"),
        ("max_price_jump", "Maximum Price Jump"),
        ("change_frequency", "Change Frequency"),
    ]

    for column, (metric_name, chart_title) in zip(chart_columns, stability_metrics, strict=False):
        with column:
            st.altair_chart(
                _bar_chart(summary_df, metric_name, f"{chart_title} by Strategy"),
                width="stretch",
            )


def _product_metric_long_frame(product_metrics_df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
    selected_df = product_metrics_df.loc[product_metrics_df[COL_STOCK_CODE] == stock_code].copy()
    if selected_df.empty:
        raise ValueError(f"No product-level rows found for stock_code '{stock_code}'.")

    long_df = selected_df.melt(
        id_vars=[COL_STOCK_CODE, "strategy"],
        value_vars=DASHBOARD_PRODUCT_COMPARISON_METRICS,
        var_name="metric",
        value_name="value",
    )
    long_df["metric_label"] = long_df["metric"].map(_format_metric_label)
    return long_df


def _render_product_level_comparison(product_metrics_df: pd.DataFrame) -> None:
    st.subheader(DASHBOARD_SECTION_TITLES["product_comparison"])
    st.caption("Supporting evidence for discussion and appendix material rather than the primary conclusion.")
    stock_codes = sorted(product_metrics_df[COL_STOCK_CODE].unique().tolist())
    default_stock_code = sorted(stock_codes)[0]
    selected_stock_code = st.selectbox(
        "Select stock_code",
        options=stock_codes,
        index=stock_codes.index(default_stock_code),
    )

    comparison_long_df = _product_metric_long_frame(product_metrics_df, selected_stock_code)
    chart = (
        alt.Chart(comparison_long_df)
        .mark_bar()
        .encode(
            x=alt.X("strategy:N", title="Strategy", sort=sorted(comparison_long_df["strategy"].unique().tolist())),
            y=alt.Y("value:Q", title="Metric Value"),
            color=alt.Color("strategy:N", legend=None),
            column=alt.Column("metric_label:N", title=None, spacing=12),
            tooltip=[
                alt.Tooltip(f"{COL_STOCK_CODE}:N", title="Stock Code"),
                alt.Tooltip("strategy:N", title="Strategy"),
                alt.Tooltip("metric_label:N", title="Metric"),
                alt.Tooltip("value:Q", title="Value", format=",.6f"),
            ],
        )
        .properties(height=300)
    )
    st.altair_chart(chart, width="stretch")

    selected_table = (
        product_metrics_df.loc[
            product_metrics_df[COL_STOCK_CODE] == selected_stock_code,
            ["strategy", *DASHBOARD_PRODUCT_COMPARISON_METRICS],
        ]
        .sort_values("strategy", kind="mergesort")
        .reset_index(drop=True)
    )
    for metric_name in DASHBOARD_PRODUCT_COMPARISON_METRICS:
        selected_table[metric_name] = selected_table[metric_name].map(lambda value: round(float(value), 6))
    st.dataframe(selected_table, width="stretch", hide_index=True)


def _boxplot(dataframe: pd.DataFrame, metric_name: str, title: str) -> alt.Chart:
    return (
        alt.Chart(dataframe)
        .mark_boxplot(extent="min-max")
        .encode(
            x=alt.X("strategy:N", title="Strategy", sort=sorted(dataframe["strategy"].unique().tolist())),
            y=alt.Y(f"{metric_name}:Q", title=_format_metric_label(metric_name)),
            color=alt.Color("strategy:N", legend=None),
            tooltip=[alt.Tooltip("strategy:N", title="Strategy")],
        )
        .properties(height=320, title=title)
    )


def _render_distribution_analysis(product_metrics_df: pd.DataFrame) -> None:
    st.subheader(DASHBOARD_SECTION_TITLES["distribution"])
    st.caption("Distribution plots provide supporting context for product-level variation across strategies.")
    left_column, right_column = st.columns(2)
    with left_column:
        st.altair_chart(
            _boxplot(product_metrics_df, "mean_daily_revenue", "Mean Daily Revenue Distribution by Strategy"),
            width="stretch",
        )
    with right_column:
        st.altair_chart(
            _boxplot(product_metrics_df, "mean_absolute_change", "Mean Absolute Change Distribution by Strategy"),
            width="stretch",
        )


def _statistical_results_frame(
    statistical_payload: dict[str, dict[str, dict[str, dict[str, float]]]]
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for section_name, metric_name in DASHBOARD_STATISTICAL_TEST_LABELS.items():
        for comparison_name, tests in statistical_payload[section_name].items():
            for test_name, test_values in tests.items():
                p_value = float(test_values["p_value"])
                rows.append(
                    {
                        "Comparison": comparison_name,
                        "Metric": metric_name,
                        "Test": DASHBOARD_TEST_LABELS.get(test_name, test_name),
                        "Statistic": float(test_values["statistic"]),
                        "p-value": p_value,
                        "Sample Size": int(test_values["sample_size"]),
                        "Significant": p_value < DASHBOARD_SIGNIFICANCE_THRESHOLD,
                    }
                )

    results_df = pd.DataFrame(rows)
    return results_df.sort_values(["Metric", "Comparison", "Test"], kind="mergesort").reset_index(drop=True)


def _render_statistical_tests(statistical_payload: dict[str, dict[str, dict[str, dict[str, float]]]]) -> None:
    st.subheader(DASHBOARD_SECTION_TITLES["statistical_tests"])
    st.caption("Results are interpreted at alpha = 0.05 using both paired t-tests and Wilcoxon signed-rank tests.")
    results_df = _statistical_results_frame(statistical_payload)
    significant_df = results_df.loc[results_df["Significant"]].reset_index(drop=True)
    mixed_df = results_df.loc[~results_df["Significant"]].reset_index(drop=True)

    if not significant_df.empty and mixed_df.empty:
        st.markdown("Interpretation: all reported pairwise results are statistically significant at alpha = 0.05.")
    elif not significant_df.empty:
        stability_all_significant = bool(
            results_df.loc[results_df["Metric"] == "abs_price_change", "Significant"].all()
        )
        revenue_mixed = bool(
            (~results_df.loc[results_df["Metric"] == "predicted_revenue", "Significant"]).any()
        )
        interpretation_parts = []
        if stability_all_significant:
            interpretation_parts.append("stability differences involving the hybrid strategy are significant across both tests")
        if revenue_mixed:
            interpretation_parts.append("revenue evidence is mixed for the hybrid versus rule comparison")
        if interpretation_parts:
            st.markdown(f"Interpretation: {'; '.join(interpretation_parts)}.")

    if not significant_df.empty:
        st.markdown("**Significant results**")
        for _, row in significant_df.iterrows():
            metric_label = "Revenue" if row["Metric"] == "predicted_revenue" else "Mean Absolute Change"
            st.markdown(
                (
                    f"- {metric_label}: {row['Comparison']} ({row['Test']}, p = {float(row['p-value']):.6g})"
                )
            )

    display_df = results_df.copy()
    display_df["Metric"] = display_df["Metric"].map(
        {
            "predicted_revenue": "Revenue",
            "abs_price_change": "Mean Absolute Change",
        }
    )
    display_df["Statistic"] = display_df["Statistic"].map(lambda value: round(float(value), 6))
    display_df["p-value"] = display_df["p-value"].map(lambda value: f"{float(value):.6g}")
    display_df["Conclusion"] = display_df["Significant"].map(
        lambda is_significant: "Significant" if bool(is_significant) else "Not significant"
    )
    display_df["_significance_order"] = display_df["Conclusion"].map(
        {"Significant": 0, "Not significant": 1}
    )
    display_df = display_df.sort_values(
        ["_significance_order", "Metric", "Comparison", "Test"],
        ascending=[True, True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    display_df = display_df[
        ["Metric", "Comparison", "Test", "Statistic", "p-value", "Sample Size", "Conclusion"]
    ]
    st.dataframe(display_df, width="stretch", hide_index=True)


def main() -> None:
    configure_logging(targets=command_logging_targets(DASHBOARD_COMMAND))
    st.set_page_config(page_title="Dynamic Pricing Study Dashboard", layout="wide")
    st.title("Dynamic Pricing Strategy Dashboard")
    st.caption("Read-only Dashboard backed exclusively by Evaluation artifacts.")

    try:
        product_metrics_df, summary_payload, statistical_payload = load_dashboard_inputs()
    except Exception as exc:
        logger.exception("Dashboard failed to load required artifacts.")
        st.error(str(exc))
        st.stop()

    logger.info(
        "Dashboard loaded successfully. Product metric rows: %s | Strategies: %s | Stock codes: %s | Inputs: %s",
        len(product_metrics_df),
        sorted(product_metrics_df["strategy"].unique().tolist()),
        sorted(product_metrics_df[COL_STOCK_CODE].unique().tolist()),
        _evaluation_input_paths(),
    )

    summary_df = _summary_frame(summary_payload)
    _render_kpi_summary(summary_df)
    _render_revenue_comparison(summary_df)
    _render_stability_comparison(summary_df)
    _render_statistical_tests(statistical_payload)
    _render_product_level_comparison(product_metrics_df)
    _render_distribution_analysis(product_metrics_df)


if __name__ == "__main__":
    main()
