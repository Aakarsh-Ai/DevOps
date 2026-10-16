from io import StringIO

import pandas as pd
import pytest

from log_analyzer import (
    detect_error_spikes,
    extract_exception,
    load_logs,
    summarize_exceptions,
    summarize_levels,
    summarize_services,
)


def test_extract_exception():
    assert (
        extract_exception("ConnectionError: database unavailable") == "ConnectionError"
    )

    assert (
        extract_exception("PaymentTimeoutError: gateway timed out")
        == "PaymentTimeoutError"
    )

    assert extract_exception("Request completed successfully") == "Other"


def test_summarize_levels():
    df = pd.DataFrame({"level": ["INFO", "ERROR", "ERROR", "WARN"]})

    result = summarize_levels(df).set_index("level")["count"].to_dict()

    assert result == {"ERROR": 2, "INFO": 1, "WARN": 1}


def test_summarize_services():
    df = pd.DataFrame(
        {
            "service": [
                "auth-service",
                "payment-service",
                "auth-service",
            ]
        }
    )

    result = summarize_services(df).set_index("service")["count"].to_dict()

    assert result == {
        "auth-service": 2,
        "payment-service": 1,
    }


def test_summarize_exceptions():
    df = pd.DataFrame(
        {
            "level": ["ERROR", "ERROR", "INFO"],
            "message": [
                "ConnectionError: database unavailable",
                "ConnectionError: retry failed",
                "Login successful",
            ],
        }
    )

    result = summarize_exceptions(df).set_index("exception")["count"].to_dict()

    assert result == {"ConnectionError": 2}


def test_detect_error_spikes():
    df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-10-16 09:00:01",
                    "2026-10-16 09:00:15",
                    "2026-10-16 09:00:30",
                    "2026-10-16 09:01:05",
                ]
            ),
            "level": ["ERROR", "ERROR", "ERROR", "ERROR"],
        }
    )

    result = detect_error_spikes(df, threshold=3)

    assert len(result) == 1
    assert result.iloc[0]["error_count"] == 3


def test_load_logs_valid_csv():
    csv_data = StringIO(
        "timestamp,service,level,message\n"
        "2026-10-16 09:00:00,auth-service,INFO,Login successful\n"
    )

    result = load_logs(csv_data)

    assert len(result) == 1
    assert result.iloc[0]["service"] == "auth-service"
    assert result.iloc[0]["level"] == "INFO"


def test_load_logs_rejects_missing_columns():
    csv_data = StringIO("timestamp\n" "2026-10-16 09:00:00\n")

    with pytest.raises(ValueError, match="Missing required columns"):
        load_logs(csv_data)
