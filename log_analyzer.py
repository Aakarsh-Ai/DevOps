import re

import pandas as pd

REQUIRED_COLUMNS = {"timestamp", "service", "level", "message"}


def load_logs(file):
    """Load CSV logs and validate their required columns."""
    df = pd.read_csv(file)

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["service"] = df["service"].fillna("unknown").astype(str)
    df["level"] = df["level"].fillna("UNKNOWN").astype(str).str.upper()
    df["message"] = df["message"].fillna("").astype(str)

    df = df.dropna(subset=["timestamp"]).copy()

    return df.sort_values("timestamp").reset_index(drop=True)


def summarize_levels(df):
    """Count log entries by severity."""
    return df["level"].value_counts().rename_axis("level").reset_index(name="count")


def summarize_services(df):
    """Count log entries by service."""
    return df["service"].value_counts().rename_axis("service").reset_index(name="count")


def extract_exception(message):
    """Extract an exception or error type from a log message."""
    match = re.search(
        r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception))\b",
        message,
    )

    return match.group(1) if match else "Other"


def summarize_exceptions(df):
    """Count exception types among ERROR entries."""
    errors = df[df["level"] == "ERROR"].copy()

    if errors.empty:
        return pd.DataFrame(columns=["exception", "count"])

    errors["exception"] = errors["message"].apply(extract_exception)

    return (
        errors["exception"]
        .value_counts()
        .rename_axis("exception")
        .reset_index(name="count")
    )


def detect_error_spikes(df, window="1min", threshold=3):
    """Flag time windows containing at least threshold ERROR entries."""
    errors = df[df["level"] == "ERROR"].copy()

    if errors.empty:
        return pd.DataFrame(columns=["window", "error_count"])

    errors["window"] = errors["timestamp"].dt.floor(window)

    spikes = errors.groupby("window").size().reset_index(name="error_count")

    return spikes[spikes["error_count"] >= threshold].reset_index(drop=True)
