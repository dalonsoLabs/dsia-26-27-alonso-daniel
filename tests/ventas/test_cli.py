"""CLI de ventas con rutas temporales y un smoke test del punto de entrada."""

from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from ventas_app.cli import main, parse_arguments


def test_parse_arguments():
    args = parse_arguments(["--input", "in.csv", "--output", "out.csv"])
    assert args.input == Path("in.csv") and args.output == Path("out.csv")


def test_cli_exports_valid_and_rejected(tmp_path, sales_frame, caplog):
    source = tmp_path / "ventas.csv"
    output = tmp_path / "reports" / "limpias.csv"
    sales_frame.to_csv(source, index=False)
    with caplog.at_level("INFO"):
        main(["--input", str(source), "--output", str(output)])
    assert len(pd.read_csv(output)) == 2
    assert len(pd.read_csv(output.with_name("limpias_invalidas.csv"))) == 1
    assert "Importe por región" in caplog.text


def test_cli_missing_input_fails(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["--input", str(tmp_path / "missing.csv"), "--output", str(tmp_path / "out.csv")])
    assert error.value.code == 1


def test_cli_bad_schema_fails(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("x\n1\n", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["--input", str(source), "--output", str(tmp_path / "out.csv")])
    assert error.value.code == 1


def test_cli_output_error_is_controlled(tmp_path, sales_frame):
    source = tmp_path / "sales.csv"
    sales_frame.to_csv(source, index=False)
    blocked = tmp_path / "blocked"
    blocked.write_text("archivo", encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["--input", str(source), "--output", str(blocked / "out.csv")])
    assert error.value.code == 1


@pytest.mark.parametrize("collision", ["direct", "invalidas", "symlink", "hardlink"])
def test_cli_preserves_source_on_output_collision(tmp_path, sales_frame, collision):
    source = tmp_path / ("clean_invalidas.csv" if collision == "invalidas" else "source.csv")
    sales_frame.to_csv(source, index=False)
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
    if collision == "invalidas":
        assert not output.exists()


@pytest.mark.integration
def test_python_module_entrypoint(tmp_path, sales_frame):
    source = tmp_path / "sales.csv"
    output = tmp_path / "out.csv"
    sales_frame.to_csv(source, index=False)
    result = subprocess.run(
        [sys.executable, "-m", "ventas_app.cli", "--input", str(source), "--output", str(output)],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert len(pd.read_csv(output)) == 2
