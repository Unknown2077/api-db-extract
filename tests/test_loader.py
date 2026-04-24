"""Unit tests: loader — including partial batch failure.

Tests:
  1. All records loaded → loaded count = len(batch), checkpoint should advance.
  2. Partial failure → loaded + failed counts correct, failed records to dead-letter.
  3. Total 4xx failure → entire batch dead-lettered, no ConnectorError raised.
  4. Total network failure → ConnectorError raised (checkpoint must NOT advance).
  5. Dry-run → no HTTP call, all records counted as loaded.
"""
import json
import os
import tempfile

import pytest
import respx
import httpx

from src.config import AppConfig
from src.report.run_report import RunReport
from src.target.loader import load_batch
from src.target.target_api_client import TargetAPIClient
from src.types import CanonicalRecord
from src.errors import ConnectorError


def _config(base_url: str) -> AppConfig:
    return AppConfig(
        target_api_base_url=base_url,
        target_api_account_uid="acc-1",
        target_api_dataset_uid_inaproc="ds-inaproc",
        target_api_dataset_uid_worldbank="ds-wb",
        target_api_token="tok",
        target_api_insert_path="/api/v1/accounts/{account_uid}/datasets/{dataset_uid}/data",
        target_api_timeout_seconds=5,
        inaproc_graphql_url="",
        inaproc_timeout_seconds=5,
        worldbank_api_url="",
        worldbank_timeout_seconds=5,
        batch_size=10,
        max_retries=1,
        retry_delay_seconds=0,
        output_dir="",
        log_level="WARNING",
    )


def _records(n: int) -> list[CanonicalRecord]:
    return [
        CanonicalRecord(
            source_system="inaproc",
            source_url="https://x.com",
            source_record_id=f"id-{i}",
            entity_name=f"Entity {i}",
            raw_payload={"id": f"id-{i}"},
        )
        for i in range(n)
    ]


@respx.mock
def test_all_records_loaded():
    url = "http://target/api/v1/accounts/acc-1/datasets/ds-inaproc/data"
    respx.post(url).mock(return_value=httpx.Response(200, json={"inserted": 3, "errors": []}))

    with tempfile.TemporaryDirectory() as tmpdir:
        config = _config("http://target")
        config = AppConfig(**{**config.__dict__, "output_dir": tmpdir})
        report = RunReport(source="inaproc", mode="incremental", dry_run=False, run_id="r1")

        with TargetAPIClient(config) as client:
            result = load_batch(_records(3), client, "ds-inaproc", "inaproc", "r1", tmpdir, False, report)

    assert result.loaded == 3
    assert result.failed == 0
    assert report.loaded == 3
    assert report.failed == 0


@respx.mock
def test_partial_batch_failure():
    """Records at index 1 fails; index 0 and 2 succeed."""
    url = "http://target/api/v1/accounts/acc-1/datasets/ds-inaproc/data"
    respx.post(url).mock(
        return_value=httpx.Response(
            200,
            json={"inserted": 2, "errors": [{"index": 1, "message": "duplicate key"}]},
        )
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        config = AppConfig(**{**_config("http://target").__dict__, "output_dir": tmpdir})
        report = RunReport(source="inaproc", mode="incremental", dry_run=False, run_id="r1")

        with TargetAPIClient(config) as client:
            result = load_batch(_records(3), client, "ds-inaproc", "inaproc", "r1", tmpdir, False, report)

        # Counts
        assert result.failed == 1
        assert report.loaded == 2
        assert report.failed == 1

        # Failed record written to dead-letter
        dl_files = [f for f in os.listdir(tmpdir) if f.startswith("dead_letter")]
        assert len(dl_files) == 1
        entries = [json.loads(line) for line in open(os.path.join(tmpdir, dl_files[0]))]
        assert len(entries) == 1
        assert entries[0]["record"]["source_record_id"] == "id-1"
        assert entries[0]["stage"] == "loader"

        # Successful records NOT in dead-letter
        loaded_ids = {e["record"]["source_record_id"] for e in entries}
        assert "id-0" not in loaded_ids
        assert "id-2" not in loaded_ids


@respx.mock
def test_total_4xx_dead_letters_entire_batch():
    url = "http://target/api/v1/accounts/acc-1/datasets/ds-inaproc/data"
    respx.post(url).mock(return_value=httpx.Response(400, text="Bad payload"))

    with tempfile.TemporaryDirectory() as tmpdir:
        config = AppConfig(**{**_config("http://target").__dict__, "output_dir": tmpdir})
        report = RunReport(source="inaproc", mode="incremental", dry_run=False, run_id="r1")

        with TargetAPIClient(config) as client:
            result = load_batch(_records(2), client, "ds-inaproc", "inaproc", "r1", tmpdir, False, report)

    assert result.loaded == 0
    assert result.failed == 2
    assert report.failed == 2


@respx.mock
def test_network_failure_raises_connector_error():
    url = "http://target/api/v1/accounts/acc-1/datasets/ds-inaproc/data"
    respx.post(url).mock(side_effect=httpx.NetworkError("connection reset"))

    with tempfile.TemporaryDirectory() as tmpdir:
        config = AppConfig(**{**_config("http://target").__dict__, "output_dir": tmpdir})
        report = RunReport(source="inaproc", mode="incremental", dry_run=False, run_id="r1")

        with TargetAPIClient(config) as client:
            with pytest.raises(ConnectorError):
                load_batch(_records(2), client, "ds-inaproc", "inaproc", "r1", tmpdir, False, report)


def test_dry_run_skips_http_and_counts_all_loaded():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = AppConfig(**{**_config("http://target").__dict__, "output_dir": tmpdir})
        report = RunReport(source="inaproc", mode="incremental", dry_run=True, run_id="r1")

        with TargetAPIClient(config) as client:
            result = load_batch(_records(5), client, "ds-inaproc", "inaproc", "r1", tmpdir, True, report)

    assert result.loaded == 5
    assert result.failed == 0
    assert report.loaded == 5
