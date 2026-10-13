""">> CLI de acciones con datos ficticios y exportaciones comprobables."""

from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from acciones_app.cli import main, parse_arguments


def test_parse_arguments():
    args = parse_arguments(["--input", "bars.csv", "--output", "clean.csv"])
    assert args.input == Path("bars.csv") and args.output == Path("clean.csv")


def test_cli_exports_bars_rejections_and_metrics(tmp_path, bars_frame, caplog):
    frame = bars_frame.copy()
    frame.loc[0, "volume"] = -1
    source = tmp_path / "bars.csv"
    frame.to_csv(source, index=False)
    output = tmp_path / "reports" / "clean.csv"
    with caplog.at_level("INFO"):
        main(["--input", str(source), "--output", str(output)])
    assert len(pd.read_csv(output)) == 5
    assert len(pd.read_csv(output.with_name("clean_invalidas.csv"))) == 1
    for name in ("rentabilidad", "volumen", "volatilidad"):
        assert len(pd.read_csv(output.with_name(f"clean_{name}.csv"))) == 2
        assert name in caplog.text


def test_cli_all_invalid_still_exports_reports(tmp_path, bars_frame):
    source = tmp_path / "bars.csv"
    frame = bars_frame.copy()
    frame["volume"] = -1
    frame.to_csv(source, index=False)
    output = tmp_path / "clean.csv"
    main(["--input", str(source), "--output", str(output)])
    assert pd.read_csv(output).empty
    assert len(pd.read_csv(tmp_path / "clean_invalidas.csv")) == 6


def test_cli_missing_input_fails(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(tmp_path / "missing.csv"), "--output", str(tmp_path / "out.csv")])
    assert error.value.code == 1


def test_cli_missing_schema_fails(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("symbol\nAAA\n", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["--input", str(source), "--output", str(tmp_path / "out.csv")])
    assert error.value.code == 1


def test_cli_output_error_is_controlled(tmp_path, bars_frame):
    source = tmp_path / "bars.csv"
    bars_frame.to_csv(source, index=False)
    blocked = tmp_path / "blocked"
    blocked.write_text("archivo", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["--input", str(source), "--output", str(blocked / "out.csv")])
    assert error.value.code == 1


@pytest.mark.parametrize("collision", ["direct", "invalidas", "rentabilidad", "volumen", "volatilidad", "symlink", "hardlink"])
def test_cli_preserves_source_on_output_collision(tmp_path, bars_frame, collision):
    reports = {"invalidas", "rentabilidad", "volumen", "volatilidad"}
    source = tmp_path / (f"clean_{collision}.csv" if collision in reports else "source.csv")
    bars_frame.to_csv(source, index=False)
    original = source.read_bytes()
    output = source if collision == "direct" else tmp_path / "clean.csv"
    if collision == "symlink":
        output.symlink_to(source)
    elif collision == "hardlink":
        output.hardlink_to(source)
    with pytest.raises(SystemExit) as error:
        main(["--input", str(source), "--output", str(output)])
    assert error.value.code == 1
    assert source.read_bytes() == original
    if collision in reports:
        assert not output.exists()


@pytest.mark.integration
def test_python_module_entrypoint(tmp_path, bars_frame):
    source = tmp_path / "synthetic.csv"
    output = tmp_path / "clean.csv"
    bars_frame.to_csv(source, index=False)
    result = subprocess.run(
        [sys.executable, "-m", "acciones_app.cli", "--input", str(source), "--output", str(output)],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert len(pd.read_csv(output)) == 6
    returns = pd.read_csv(tmp_path / "clean_rentabilidad.csv").set_index("symbol")
    assert returns.loc["AAA", "return_pct"] == pytest.approx(-1)
