"""
Comprehensive test suite for svgclean-cli.
TDD coverage: XSS script stripping, event handler neutralization,
dangerous URI sanitation, editor bloat pruning, coordinate precision limiter,
file & batch directory processing, and CLI interactive mode.
"""
import os
import tempfile
import pytest

from svgclean.core import clean_svg, clean_file, clean_directory, SvgResult
from svgclean.cli import main


# ---------------------------------------------------------------------------
# Security Sanitization Tests
# ---------------------------------------------------------------------------

def test_xss_script_tag_removal():
    raw_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <script type="text/javascript">alert('XSS vulnerability!');</script>
        <circle cx="50" cy="50" r="40" fill="red" />
    </svg>"""
    result: SvgResult = clean_svg(raw_svg)
    assert "<script" not in result.cleaned_svg
    assert "alert" not in result.cleaned_svg
    assert "<circle" in result.cleaned_svg
    assert any("script" in t.lower() for t in result.threats_removed)


def test_event_handler_stripping():
    raw_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" onload="stealCookies()">
        <rect width="100" height="100" onclick="evilAction()" onmouseover="track()" />
    </svg>"""
    result = clean_svg(raw_svg)
    assert "onload" not in result.cleaned_svg
    assert "onclick" not in result.cleaned_svg
    assert "onmouseover" not in result.cleaned_svg
    assert "stealCookies" not in result.cleaned_svg
    assert "rect" in result.cleaned_svg


def test_dangerous_uri_neutralization():
    raw_svg = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
        <a href="javascript:alert(1)">
            <text x="10" y="20">Click me</text>
        </a>
        <image xlink:href="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==" />
    </svg>"""
    result = clean_svg(raw_svg)
    assert "javascript:" not in result.cleaned_svg
    assert "data:text/html" not in result.cleaned_svg


def test_dangerous_elements_blacklisted():
    raw_svg = """<svg xmlns="http://www.w3.org/2000/svg">
        <foreignObject width="100" height="100">
            <iframe src="https://attacker.com/exploit.html"></iframe>
        </foreignObject>
        <path d="M 0 0 L 10 10" />
    </svg>"""
    result = clean_svg(raw_svg)
    assert "foreignObject" not in result.cleaned_svg
    assert "iframe" not in result.cleaned_svg
    assert "path" in result.cleaned_svg


# ---------------------------------------------------------------------------
# Minification & Bloat Pruning Tests
# ---------------------------------------------------------------------------

def test_editor_metadata_and_namespaces():
    raw_svg = """<svg xmlns="http://www.w3.org/2000/svg"
        xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
        xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd">
        <sodipodi:namedview pagecolor="#ffffff" />
        <metadata id="metadata1">
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
                <cc:Work xmlns:cc="http://creativecommons.org/ns#" />
            </rdf:RDF>
        </metadata>
        <circle cx="10" cy="10" r="5" inkscape:label="Layer 1" />
    </svg>"""
    result = clean_svg(raw_svg, remove_metadata=True)
    assert "<metadata" not in result.cleaned_svg
    assert "namedview" not in result.cleaned_svg
    assert "inkscape:label" not in result.cleaned_svg


def test_coordinate_precision_rounding():
    raw_svg = '<svg viewBox="0 0 100 100"><path d="M 12.345678 45.678912 L 89.123456 99.987654" /></svg>'
    result = clean_svg(raw_svg, precision=2)
    assert "12.35" in result.cleaned_svg
    assert "45.68" in result.cleaned_svg
    assert "12.345678" not in result.cleaned_svg
    assert result.saved_bytes > 0


def test_empty_groups_pruning():
    raw_svg = '<svg viewBox="0 0 100 100"><g id="empty1"></g><g><circle cx="5" cy="5" r="2"/></g></svg>'
    result = clean_svg(raw_svg)
    assert 'id="empty1"' not in result.cleaned_svg
    assert "<circle" in result.cleaned_svg


# ---------------------------------------------------------------------------
# File & Directory Batch Processing
# ---------------------------------------------------------------------------

def test_clean_file(tmp_path):
    svg_in = tmp_path / "graphic.svg"
    svg_out = tmp_path / "cleaned.svg"

    svg_in.write_text('<svg viewBox="0 0 10"><script>alert(1)</script><circle cx="1.23456" cy="2"/></svg>', encoding="utf-8")

    res = clean_file(str(svg_in), str(svg_out), precision=2)
    assert os.path.exists(svg_out)
    assert res.threats_count >= 1
    content = svg_out.read_text(encoding="utf-8")
    assert "<script" not in content
    assert "1.23" in content


def test_clean_directory(tmp_path):
    in_dir = tmp_path / "icons"
    out_dir = tmp_path / "clean_icons"
    in_dir.mkdir()

    (in_dir / "icon1.svg").write_text('<svg><script>alert(1)</script><rect/></svg>', encoding="utf-8")
    (in_dir / "icon2.svg").write_text('<svg><circle onclick="run()"/></svg>', encoding="utf-8")

    summary = clean_directory(str(in_dir), str(out_dir))
    assert summary["files_processed"] == 2
    assert summary["total_threats_neutralized"] >= 2
    assert (out_dir / "icon1.svg").exists()
    assert (out_dir / "icon2.svg").exists()


# ---------------------------------------------------------------------------
# CLI Commands and Interactive Tests
# ---------------------------------------------------------------------------

def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "svgclean-cli" in captured.out or "0.1.0" in captured.out


def test_cli_dry_run(tmp_path, capsys):
    svg_file = tmp_path / "test.svg"
    svg_file.write_text('<svg><script>bad()</script><rect width="10.8888"/></svg>', encoding="utf-8")

    exit_code = main([str(svg_file), "--dry-run"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Dry-Run" in captured.out
    assert "Threats Neutralized" in captured.out


def test_cli_interactive_wizard(tmp_path, monkeypatch, capsys):
    svg_file = tmp_path / "wizard.svg"
    svg_file.write_text('<svg><circle onclick="leak()"/></svg>', encoding="utf-8")
    out_file = tmp_path / "wizard_clean.svg"

    # Interactive prompts:
    # 1. Action: 1 (Single SVG file)
    # 2. Input path: str(svg_file)
    # 3. Output path: str(out_file)
    # 4. Precision: 2
    # 5. Strip scripts: y
    # 6. Remove metadata: y
    # 7. Dry run: n
    inputs = iter([
        "1",
        str(svg_file),
        str(out_file),
        "2",
        "y",
        "y",
        "n",
    ])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    exit_code = main(["--interactive"])
    assert exit_code == 0
    assert out_file.exists()
    cleaned = out_file.read_text(encoding="utf-8")
    assert "onclick" not in cleaned
