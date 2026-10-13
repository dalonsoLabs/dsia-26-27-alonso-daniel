"""Lectura del esquema tabular y de los campos compactos de la API."""

import gzip
import json

import pandas as pd
import pytest

from acciones_app.loader import API_FIELDS, DataLoadError, load


def test_csv_load(tmp_path, bars_frame):
    path = tmp_path / "bars.csv"
    bars_frame.to_csv(path, index=False)
    pd.testing.assert_frame_equal(load(path), bars_frame, check_dtype=False)


@pytest.mark.parametrize("suffix", ["jsonl", "jsonl.gz", "JSONL.GZ"])
def test_jsonl_normalizes_api_fields(tmp_path, bars_frame, suffix):
    compressed = suffix.lower().endswith(".gz")
    path = tmp_path / f"bars.{suffix}"
    reverse = {value: key for key, value in API_FIELDS.items()}
    opener = gzip.open if compressed else open
    with opener(path, "wt", encoding="utf-8") as sink:
        for record in bars_frame.to_dict("records"):
            sink.write(json.dumps({reverse.get(key, key): value for key, value in record.items()}) + "\n")
    pd.testing.assert_frame_equal(load(path), bars_frame, check_dtype=False)


@pytest.mark.parametrize("suffix", ["csv", "jsonl", "jsonl.gz"])
def test_missing_file_is_domain_error(tmp_path, suffix):
    with pytest.raises(DataLoadError):
        load(tmp_path / f"missing.{suffix}")


@pytest.mark.parametrize("content", ["{\n", "[]\n", '{"t":"x","timestamp":"y"}\n'])
def test_malformed_jsonl_is_domain_error(tmp_path, content):
    path = tmp_path / "bad.jsonl"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(DataLoadError):
        load(path)


def test_corrupt_gzip_is_domain_error(tmp_path):
    path = tmp_path / "bad.jsonl.gz"
    path.write_bytes(b"not a gzip archive")
    with pytest.raises(DataLoadError):
        load(path)


def test_empty_csv_is_domain_error(tmp_path):
    path = tmp_path / "empty.csv"
    path.touch()
    with pytest.raises(DataLoadError):
        load(path)


def test_unsupported_format(tmp_path):
    with pytest.raises(DataLoadError, match="Formato no soportado"):
        load(tmp_path / "snapshots.json")
