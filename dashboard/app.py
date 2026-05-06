import json
import logging
from pathlib import Path
import sys

import altair as alt
import pandas as pd
import pyarrow.parquet as pq
import streamlit as st

# Ensure project-root imports work when Streamlit executes this file directly.
if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import (
    CLEAN_DATA_PATH,
    COL_STOCK_CODE,
    DAILY_AGG_DATA_PATH,
    DASHBOARD_COMMAND,
    DASHBOARD_HIGHLIGHT_BAR_COLOR,
    DASHBOARD_LEADER_CELL_STYLE,
    DASHBOARD_MUTED_BAR_COLOR,
    DASHBOARD_NONSIGNIFICANT_CELL_STYLE,
    DASHBOARD_PRIMARY_METRICS,
    EVALUATION_PRODUCT_METRIC_LEVEL,
    EVALUATION_STATISTICAL_TESTS_PATH,
    EVALUATION_STRATEGY_METRICS_PATH,
    EVALUATION_STRATEGY_SUMMARY_PATH,
    DASHBOARD_PRODUCT_COMPARISON_METRICS,
    DASHBOARD_PRODUCT_METRIC_COLUMNS,
    DASHBOARD_SECTION_TITLES,
    DASHBOARD_SIGNIFICANCE_THRESHOLD,
    DASHBOARD_SIGNIFICANT_CELL_STYLE,
    DASHBOARD_STABILITY_SUPPORTING_METRICS,
    DASHBOARD_STATISTICAL_TEST_LABELS,
    DASHBOARD_SUPPORTING_METRICS,
    DASHBOARD_SUMMARY_METRICS,
    DASHBOARD_TEST_LABELS,
    FEATURE_TEST_DATA_PATH,
    FEATURE_TRAIN_DATA_PATH,
    HYBRID_SMOOTHING_ALPHA,
    MAX_DAILY_CHANGE,
    MODEL_FEATURE_COLUMNS,
    MODEL_TYPE,
    PRICE_GRID_PERCENTAGE,
    PRODUCT_SELECTION_REPORT_FILE,
    PROJECT_ROOT,
    RAW_INSPECTION_REPORT_FILE,
    REPORTS_PATH,
    RULE_PRICE_INCREASE,
    SIMULATION_GRID_POINTS,
    SIMULATION_STRATEGIES,
    TRAIN_SPLIT_RATIO,
)
from pipeline.execution import command_logging_targets
from preprocessing.common import configured_path
from utils.data_contracts import (
    validate_evaluation_metrics,
    validate_evaluation_summary,
    validate_evaluation_tests,
)
from utils.logging_config import configure_logging

logger = logging.getLogger("dashboard.app")


def _format_metric_label(metric_name: str) -> str:
    return metric_name.replace("_", " ").title()


def _format_number(value: float) -> str:
    return f"{value:,.6f}" if abs(value) < 10 else f"{value:,.3f}"


def _metric_prefers_higher(metric_name: str) -> bool:
    return metric_name in {"total_revenue", "mean_daily_revenue"}


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


def _parquet_row_count(path: Path) -> int:
    return pq.read_metadata(path).num_rows


@st.cache_data(show_spinner=False)
def load_dataset_overview() -> dict[str, int]:
    raw_inspection = json.loads(
        configured_path(PROJECT_ROOT, REPORTS_PATH + RAW_INSPECTION_REPORT_FILE).read_text(encoding="utf-8")
    )
    product_selection = json.loads(
        configured_path(PROJECT_ROOT, REPORTS_PATH + PRODUCT_SELECTION_REPORT_FILE).read_text(encoding="utf-8")
    )
    train_rows = _parquet_row_count(configured_path(PROJECT_ROOT, FEATURE_TRAIN_DATA_PATH))
    test_rows = _parquet_row_count(configured_path(PROJECT_ROOT, FEATURE_TEST_DATA_PATH))
    daily_rows = _parquet_row_count(configured_path(PROJECT_ROOT, DAILY_AGG_DATA_PATH))
    clean_rows = _parquet_row_count(configured_path(PROJECT_ROOT, CLEAN_DATA_PATH))
    return {
        "raw_records": raw_inspection["dataset_shape"]["rows"],
        "clean_records": clean_rows,
        "products_analyzed": product_selection["run_summary"]["products_analyzed"],
        "products_selected": product_selection["run_summary"]["selected_products"],
        "daily_observations": daily_rows,
        "train_observations": train_rows,
        "test_observations": test_rows,
        "modelled_observations": train_rows + test_rows,
    }


def _render_dataset_overview(overview: dict[str, int]) -> None:
    st.subheader(DASHBOARD_SECTION_TITLES["dataset_overview"])
    st.caption("Online Retail II dataset — United Kingdom transactions, 2010–2011.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Raw Transactions", f"{overview['raw_records']:,}")
        st.metric("Cleaned Transactions", f"{overview['clean_records']:,}")
    with col2:
        st.metric("Products Analysed", f"{overview['products_analyzed']:,}")
        st.metric("Products Selected", str(overview["products_selected"]))
    with col3:
        st.metric("Training Observations", f"{overview['train_observations']:,}")
        st.metric("Test Observations", f"{overview['test_observations']:,}")
    st.caption(
        f"{overview['raw_records']:,} raw → {overview['clean_records']:,} cleaned transactions → "
        f"{overview['daily_observations']:,} daily product observations → "
        f"{overview['modelled_observations']:,} modelled "
        f"({overview['train_observations']:,} train / {overview['test_observations']:,} test). "
        f"{overview['products_selected']} products selected from {overview['products_analyzed']:,} "
        f"based on revenue contribution, activity levels, and observable price variation."
    )

    st.divider()
    st.markdown("**Experiment Configuration**")
    cfg_col1, cfg_col2, cfg_col3 = st.columns(3)
    train_pct = int(TRAIN_SPLIT_RATIO * 100)
    with cfg_col1:
        st.metric("Demand Model", "Linear Regression" if MODEL_TYPE == "LinearRegression" else MODEL_TYPE)
        st.metric("Train / Test Split", f"{train_pct}% / {100 - train_pct}% (chronological)")
        st.metric("Feature Count", str(len(MODEL_FEATURE_COLUMNS)))
    with cfg_col2:
        st.metric("Rule Adjustment", f"±{int(RULE_PRICE_INCREASE * 100)}% per day")
        st.metric("ML Price Grid", f"±{int(PRICE_GRID_PERCENTAGE * 100)}%, {SIMULATION_GRID_POINTS} candidates")
    with cfg_col3:
        st.metric("Hybrid Smoothing (α)", str(HYBRID_SMOOTHING_ALPHA))
        st.metric("Hybrid Daily Cap", f"±{int(MAX_DAILY_CHANGE * 100)}%")
    st.caption(
        "Features: lag-1 demand, lag-7 demand, 7-day rolling mean demand, average daily price, "
        "7 day-of-week indicators, 12 month indicators (23 total)."
    )


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
    st.markdown(
        (
            f"Research answer: **{revenue_ranking[0].upper()}** maximises revenue, while "
            f"**{stability_ranking[0].upper()}** provides the most stable pricing, demonstrating a clear "
            "trade-off between performance and stability."
        )
    )
    st.caption(
        (
            f"This frames the core trade-off directly: revenue ranking is "
            f"{' > '.join(strategy.upper() for strategy in revenue_ranking)}, while stability ranking is "
            f"{' < '.join(strategy.upper() for strategy in stability_ranking)}."
        )
    )
    st.markdown(
        "Key takeaway: This demonstrates a trade-off: optimisation improves revenue, while constraints improve stability."
    )


def _strategy_ranking_summary_frame(summary_df: pd.DataFrame) -> pd.DataFrame:
    revenue_leader = _strategy_for_metric(summary_df, "total_revenue", ascending=False)
    stability_leader = _strategy_for_metric(summary_df, "mean_absolute_change", ascending=True)
    return pd.DataFrame(
        [
            {"Dimension": "Revenue", "Best Strategy": str(revenue_leader).upper()},
            {"Dimension": "Stability", "Best Strategy": str(stability_leader).upper()},
        ]
    )


def _render_kpi_summary(summary_df: pd.DataFrame) -> None:
    st.subheader(DASHBOARD_SECTION_TITLES["summary"])
    st.caption(
        "Primary metrics answer the research question directly. Supporting metrics remain available for interpretation only."
    )
    st.caption("Highlighted bars and cells mark the best-performing strategy for each metric.")
    _render_primary_findings(summary_df)
    ranking_summary_df = _strategy_ranking_summary_frame(summary_df)
    with st.container(border=True):
        st.markdown("**Strategy Ranking Summary**")
        st.dataframe(ranking_summary_df, width="stretch", hide_index=True)
        st.markdown(
            f"Revenue leader: **:green[{ranking_summary_df.iloc[0]['Best Strategy']}]** | "
            f"Stability leader: **:blue[{ranking_summary_df.iloc[1]['Best Strategy']}]**"
        )

    strategies = summary_df["strategy"].tolist()
    columns = st.columns(len(strategies))
    revenue_leader = _strategy_for_metric(summary_df, "total_revenue", ascending=False)
    stability_leader = _strategy_for_metric(summary_df, "mean_absolute_change", ascending=True)

    for column, strategy_name in zip(columns, strategies, strict=False):
        strategy_row = summary_df.loc[summary_df["strategy"] == strategy_name].iloc[0]
        with column:
            st.markdown(f"**{strategy_name.upper()}**")
            if strategy_name == revenue_leader:
                st.markdown("**:green[Highest revenue]**")
            elif strategy_name == stability_leader:
                st.markdown("**:blue[Lowest mean absolute change]**")
            else:
                st.caption("Supporting comparator")
            for metric_name in DASHBOARD_PRIMARY_METRICS:
                st.metric(_format_metric_label(metric_name), _format_number(float(strategy_row[metric_name])))

    st.markdown("**Supporting Metrics**")
    display_df = summary_df.copy()
    display_df = display_df[["strategy", *DASHBOARD_SUPPORTING_METRICS]]
    st.dataframe(
        _styled_metric_table(display_df, DASHBOARD_SUPPORTING_METRICS),
        width="stretch",
        hide_index=True,
    )


def _bar_chart(
    dataframe: pd.DataFrame,
    metric_name: str,
    title: str,
    *,
    highlighted_strategy: str | None = None,
) -> alt.Chart:
    chart_df = dataframe.copy()
    chart_df["is_highlight"] = chart_df["strategy"].astype(str) == str(highlighted_strategy)
    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("strategy:N", title="Strategy", sort=chart_df["strategy"].tolist()),
            y=alt.Y(f"{metric_name}:Q", title=_format_metric_label(metric_name)),
            color=alt.condition(
                "datum.is_highlight",
                alt.value(DASHBOARD_HIGHLIGHT_BAR_COLOR),
                alt.value(DASHBOARD_MUTED_BAR_COLOR),
            ),
            tooltip=[
                alt.Tooltip("strategy:N", title="Strategy"),
                alt.Tooltip(f"{metric_name}:Q", title=_format_metric_label(metric_name), format=",.6f"),
            ],
        )
        .properties(height=320, title=title)
    )


def _metric_long_frame(dataframe: pd.DataFrame, id_vars: list[str], metric_names: list[str] | tuple[str, ...]) -> pd.DataFrame:
    long_df = dataframe.melt(
        id_vars=id_vars,
        value_vars=list(metric_names),
        var_name="metric",
        value_name="value",
    )
    long_df["metric_label"] = pd.Categorical(
        long_df["metric"].map(_format_metric_label),
        categories=[_format_metric_label(metric_name) for metric_name in metric_names],
        ordered=True,
    )
    return long_df


def _mark_metric_leaders(long_df: pd.DataFrame) -> pd.DataFrame:
    marked_df = long_df.copy()
    marked_df["is_metric_leader"] = False
    for metric_name, metric_slice in marked_df.groupby("metric", sort=False):
        leader_value = metric_slice["value"].max() if _metric_prefers_higher(str(metric_name)) else metric_slice["value"].min()
        marked_df.loc[metric_slice.index, "is_metric_leader"] = metric_slice["value"].eq(leader_value)
    return marked_df


def _styled_metric_table(dataframe: pd.DataFrame, metric_names: list[str] | tuple[str, ...]):
    styles = pd.DataFrame("", index=dataframe.index, columns=dataframe.columns)
    for metric_name in metric_names:
        leader_value = (
            dataframe[metric_name].max()
            if _metric_prefers_higher(metric_name)
            else dataframe[metric_name].min()
        )
        styles.loc[dataframe[metric_name].eq(leader_value), metric_name] = DASHBOARD_LEADER_CELL_STYLE
    formatters = {metric_name: _format_number for metric_name in metric_names}
    return dataframe.style.apply(lambda _: styles, axis=None).format(formatters)


def _styled_statistical_results_table(dataframe: pd.DataFrame):
    styles = pd.DataFrame("", index=dataframe.index, columns=dataframe.columns)
    styles.loc[dataframe["Conclusion"] == "Significant", "Conclusion"] = DASHBOARD_SIGNIFICANT_CELL_STYLE
    styles.loc[dataframe["Conclusion"] == "Not significant", "Conclusion"] = DASHBOARD_NONSIGNIFICANT_CELL_STYLE
    return dataframe.style.apply(lambda _: styles, axis=None)


def _render_revenue_comparison(summary_df: pd.DataFrame) -> None:
    st.subheader(DASHBOARD_SECTION_TITLES["revenue"])
    revenue_ranking = _metric_rankings(summary_df, "total_revenue", ascending=False)
    mean_daily_revenue_leader = _strategy_for_metric(summary_df, "mean_daily_revenue", ascending=False)
    st.markdown(
        f"Interpretation: **{revenue_ranking[0].upper()}** achieves the highest total revenue under the shared simulated demand conditions."
    )
    st.caption(
        f"Mean daily revenue is shown as a secondary measure to support interpretation rather than drive the main conclusion."
    )
    st.altair_chart(
        _bar_chart(
            summary_df,
            "total_revenue",
            "Total Revenue by Strategy",
            highlighted_strategy=revenue_ranking[0],
        ),
        width="stretch",
    )
    st.altair_chart(
        _bar_chart(
            summary_df,
            "mean_daily_revenue",
            "Mean Daily Revenue by Strategy",
            highlighted_strategy=mean_daily_revenue_leader,
        ),
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
        _bar_chart(
            summary_df,
            "mean_absolute_change",
            "Mean Absolute Change by Strategy",
            highlighted_strategy=stability_leader,
        ),
        width="stretch",
    )
    for metric_name in DASHBOARD_STABILITY_SUPPORTING_METRICS:
        st.altair_chart(
            _bar_chart(
                summary_df,
                metric_name,
                f"{_format_metric_label(metric_name)} by Strategy",
                highlighted_strategy=_strategy_for_metric(summary_df, metric_name, ascending=True),
            ),
            width="stretch",
        )


def _product_metric_long_frame(product_metrics_df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
    selected_df = product_metrics_df.loc[product_metrics_df[COL_STOCK_CODE] == stock_code].copy()
    if selected_df.empty:
        raise ValueError(f"No product-level rows found for stock_code '{stock_code}'.")

    return selected_df.sort_values("strategy", kind="mergesort").reset_index(drop=True)


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

    st.caption(
        "Each metric is shown in its own full-width chart so nothing gets compressed on smaller screens."
    )
    selected_table = _product_metric_long_frame(product_metrics_df, selected_stock_code)
    for metric_name in DASHBOARD_PRODUCT_COMPARISON_METRICS:
        st.altair_chart(
            _bar_chart(
                selected_table,
                metric_name,
                f"{_format_metric_label(metric_name)} by Strategy",
                highlighted_strategy=_strategy_for_metric(
                    selected_table,
                    metric_name,
                    ascending=not _metric_prefers_higher(metric_name),
                ),
            ),
            width="stretch",
        )

    selected_table = selected_table[["strategy", *DASHBOARD_PRODUCT_COMPARISON_METRICS]]
    st.dataframe(
        _styled_metric_table(selected_table, DASHBOARD_PRODUCT_COMPARISON_METRICS),
        width="stretch",
        hide_index=True,
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
    st.caption("Significance outcomes are highlighted to separate robust findings from weaker evidence.")
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
            interpretation_parts.append(
                "revenue differences between hybrid and rule are weaker and not consistently significant across tests"
            )
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
    st.dataframe(_styled_statistical_results_table(display_df), width="stretch", hide_index=True)


def main() -> None:
    configure_logging(targets=command_logging_targets(DASHBOARD_COMMAND))
    st.set_page_config(page_title="Dynamic Pricing Study Dashboard", layout="wide")
    st.title("Dynamic Pricing Strategy Dashboard")
    st.caption("Read-only Dashboard backed exclusively by Evaluation artifacts.")
    st.caption(
        "Sections 1-4 present the core findings used to answer the research question. Section 5 provides supporting evidence."
    )

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

    try:
        overview = load_dataset_overview()
    except Exception as exc:
        logger.warning("Dataset overview artifacts unavailable: %s", exc)
        overview = None

    summary_df = _summary_frame(summary_payload)
    if overview is not None:
        _render_dataset_overview(overview)
    _render_kpi_summary(summary_df)
    _render_revenue_comparison(summary_df)
    _render_stability_comparison(summary_df)
    _render_statistical_tests(statistical_payload)
    _render_product_level_comparison(product_metrics_df)


if __name__ == "__main__":
    main()
