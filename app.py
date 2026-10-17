import pandas as pd
import plotly.express as px
import streamlit as st

from log_analyzer import (
    detect_error_spikes,
    load_logs,
    summarize_exceptions,
    summarize_levels,
    summarize_services,
)

st.set_page_config(
    page_title="Log Triage Engine",
    page_icon="📊",
    layout="wide",
)

st.title("Microservice Log Anomaly & Error Triage Engine 1.3")
st.caption(
    "Analyze application logs, identify error spikes, and investigate exceptions."
)

uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV log file",
    type=["csv"],
)

try:
    if uploaded_file is not None:
        logs = load_logs(uploaded_file)
    else:
        logs = load_logs("data/sample_logs.csv")
        st.sidebar.info("Showing built-in sample data.")

except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as error:
    st.error(f"Unable to read the log file: {error}")
    st.stop()

services = sorted(logs["service"].unique())
selected_services = st.sidebar.multiselect(
    "Filter services",
    options=services,
    default=services,
)

levels = sorted(logs["level"].unique())
selected_levels = st.sidebar.multiselect(
    "Filter severity",
    options=levels,
    default=levels,
)

filtered = logs[
    logs["service"].isin(selected_services) & logs["level"].isin(selected_levels)
].copy()

total_logs = len(filtered)
total_errors = int((filtered["level"] == "ERROR").sum())
total_warnings = int((filtered["level"] == "WARN").sum())
error_rate = total_errors / total_logs * 100 if total_logs else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total log entries", total_logs)
col2.metric("Errors", total_errors)
col3.metric("Warnings", total_warnings)
col4.metric("Error rate", f"{error_rate:.1f}%")

st.subheader("Log severity distribution")

severity_summary = summarize_levels(filtered)

if not severity_summary.empty:
    fig = px.pie(
        severity_summary,
        names="level",
        values="count",
        title="Entries by severity",
        hole=0.4,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No logs match the selected filters.")

left, right = st.columns(2)

with left:
    st.subheader("Log volume by service")
    service_summary = summarize_services(filtered)

    if not service_summary.empty:
        fig = px.bar(
            service_summary,
            x="service",
            y="count",
            title="Entries per service",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No service data to display.")

with right:
    st.subheader("Most common exceptions")
    exception_summary = summarize_exceptions(filtered)

    if not exception_summary.empty:
        fig = px.treemap(
            exception_summary,
            path=["exception"],
            values="count",
            title="Exception frequency",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No errors found in the selected logs.")

st.subheader("Error spike detection")

spikes = detect_error_spikes(filtered)

if not spikes.empty:
    st.warning("Potential error spikes detected.")
    st.dataframe(spikes, use_container_width=True)

    fig = px.bar(
        spikes,
        x="window",
        y="error_count",
        title="Error count by one-minute window",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.success("No error windows met the configured spike threshold.")

st.subheader("Filtered log entries")
st.dataframe(filtered, use_container_width=True)

st.download_button(
    "Download filtered logs",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_logs.csv",
    mime="text/csv",
)
