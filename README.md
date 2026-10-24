# svgclean-cli

[![PyPI version](https://img.shields.io/pypi/v/svgclean-cli.svg)](https://pypi.org/project/svgclean-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/svgclean-cli.svg)](https://pypi.org/project/svgclean-cli/)
[![GitHub stars](https://img.shields.io/github/stars/uchiha-fire/svgclean-cli?style=social)](https://github.com/uchiha-fire/svgclean-cli)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Shubham%20Sharma-0A66C2.svg?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/shubham-sharma-28487819b/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/uchiha-fire/svgclean-cli/blob/main/LICENSE)
[![Zephyrus Labs](https://img.shields.io/badge/Developed%20by-Zephyrus%20Labs-6366f1.svg)](https://zephyrus-labs.tech/)

A robust SVG sanitizer, minifier, and security scrubber against XSS and XML exploits by **[Zephyrus Labs](https://zephyrus-labs.tech/)** for Linux, macOS, and Windows.

---

## Features

- 🛡️ **Comprehensive XSS Scrubbing**: Strictly strips `<script>`, `<foreignObject>`, `<iframe>`, `<embed>`, `<object>`, inline event handlers (`onload`, `onclick`, `onerror`), and `javascript:` / `data:text/html` URLs.
- 💣 **XXE & Entity Bomb Defense**: Built with `defusedxml` to block XML External Entity (XXE) expansion and Billion Laughs vulnerabilities.
- 🧹 **Editor Bloat Stripping**: Eliminates design editor namespaces (`inkscape:`, `sodipodi:`, `adobe:`, `sketch:`), `<metadata>`, editor comments, and unused `<g>` wrappers.
- 📉 **Coordinate Precision Limiter**: Rounds floating-point coordinates (e.g. 8 decimals down to 2), saving 40%–70% bandwidth with zero perceptible visual quality loss.
- 📁 **Batch Directory Processing**: Sanitize entire icon libraries and vector asset folders in a single command.
- 🧪 **Dry-Run Inspection**: Audit threat vectors and calculate byte savings without modifying files on disk.
- 🧙 **Interactive Terminal Wizard**: User-friendly step-by-step wizard with real-time feedback and inline SVG pasting.

---

## Installation

```bash
pip install svgclean-cli
```

Or install the latest development build directly:

```bash
pip install git+https://github.com/uchiha-fire/svgclean-cli.git
```

---

## Interactive Mode

Run `svgclean` without arguments or pass `--interactive` to launch the wizard:

```bash
svgclean
```

```text
╔══════════════════════════════════════════════════════════════╗
║               svgclean-cli  v0.1.0                           ║
║     SVG Sanitizer, Minifier, & Security Scrubber             ║
║     Zephyrus Labs (https://zephyrus-labs.tech/)              ║
╚══════════════════════════════════════════════════════════════╝

Welcome to the svgclean Interactive Sanitizer Wizard!

Select Source Type:
  [1] Sanitize single SVG file
  [2] Batch sanitize a directory of SVG files
  [3] Paste inline raw SVG XML string
Choose [1/2/3] (default: 1): 1

Enter path to SVG file: untrusted_icon.svg
Enter output file path (default: untrusted_icon_clean.svg): untrusted_icon_clean.svg
Coordinate decimal precision [0-4] (default: 2): 2
Strip <script> tags and event handlers? [Y/n]: y
Remove editor metadata and namespaces? [Y/n]: y
Dry-run only (do not write output file)? [y/N]: n

Sanitization & Optimization Summary for untrusted_icon.svg:
-----------------------------------------------------------------
  Original Size:       14,820 bytes
  Cleaned Size:        4,310 bytes
  Bytes Saved:         10,510 bytes (70.9% reduction)
  Threats Neutralized: 2

  Neutralized Security Risks:
    - Removed unsafe element: <script>
    - Removed inline event handler: onload
-----------------------------------------------------------------

✓ Sanitized SVG saved cleanly to: untrusted_icon_clean.svg
```

---

## CLI Usage & Options

```bash
# Sanitize a single SVG file (outputs input_clean.svg)
svgclean logo.svg

# Output to a specific file
svgclean logo.svg -o ./dist/clean_logo.svg

# Batch sanitize an entire directory of icons
svgclean ./assets/icons -o ./dist/clean_icons

# Dry-run audit (reports threats and byte savings without saving)
svgclean suspicious.svg --dry-run

# Custom coordinate precision (0 to 4 decimal places)
svgclean detailed_map.svg -p 3
```

### Options Reference

| Flag | Long Option | Default | Description |
| :--- | :--- | :--- | :--- |
| `input` | *(positional)* | None | Path to SVG file or directory of SVGs |
| `-o` | `--output` | `<input>_clean` | Destination path for cleaned SVG or directory |
| `-p` | `--precision` | `2` | Number of decimal places for coordinate numbers (0–4) |
| `-d` | `--dry-run` | `False` | Report threats and savings without modifying disk |
| `-f` | `--force` | `False` | Overwrite existing output files without prompting |
| | `--keep-metadata` | `False` | Retain editor metadata (`<metadata>`, `<desc>`) |
| `-s` | `--silent` | `False` | Quiet mode (suppresses output) |
| `-i` | `--interactive` | `False` | Launch interactive terminal wizard |
| `-v` | `--version` | — | Display package version |

---

## Python API Reference

```python
from svgclean import clean_svg, clean_file, clean_directory, SvgResult

# 1. Clean inline SVG string
dirty_svg = '''
<svg viewBox="0 0 100 100">
    <script>alert("XSS")</script>
    <path d="M 10.493821 20.948215" onclick="leak()"/>
</svg>
'''

result: SvgResult = clean_svg(dirty_svg, precision=2)
print(f"Original size: {result.orig_bytes} bytes")
print(f"Cleaned size:  {result.final_bytes} bytes (Saved {result.saved_pct:.1f}%)")
print(f"Threats neutralized: {result.threats_removed}")
print(result.cleaned_svg)

# 2. Clean a file
clean_file("input.svg", "output.svg", precision=2)

# 3. Batch clean a directory
summary = clean_directory("./raw_icons", "./cleaned_icons")
print(f"Processed {summary['files_processed']} files, neutralized {summary['total_threats_neutralized']} threats.")
```

---

## Developed & Maintained by Zephyrus Labs

Built and maintained with ❤️ by **[Zephyrus Labs](https://zephyrus-labs.tech/)** and Lead Developer **[Shubham Sharma](https://www.linkedin.com/in/shubham-sharma-28487819b/)**.

- 💼 **LinkedIn**: [linkedin.com/in/shubham-sharma-28487819b](https://www.linkedin.com/in/shubham-sharma-28487819b/)
- 💻 **GitHub**: [@uchiha-fire](https://github.com/uchiha-fire)
- 🌐 **Website**: [zephyrus-labs.tech](https://zephyrus-labs.tech/)
- ✉️ **Organization Email**: [zephyrus.labs@gmail.com](mailto:zephyrus.labs@gmail.com)
- 📬 **Developer Email**: [sharmashubham25962@gmail.com](mailto:sharmashubham25962@gmail.com)

If you find this tool helpful, please give it a ⭐️ on [GitHub](https://github.com/uchiha-fire/svgclean-cli)!

---

## Acknowledgements & Attributions

This tool builds upon and credits the exceptional work of open-source projects:

- **[defusedxml](https://github.com/tiran/defusedxml)**: Hardened XML parser guarding against XML vulnerabilities and entity expansion. Licensed under Python Software Foundation License.

---

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/uchiha-fire/svgclean-cli/blob/main/LICENSE) file for details.

---

<p align="right">
  <sub>Lead Developer: <a href="https://www.linkedin.com/in/shubham-sharma-28487819b/">Shubham Sharma</a> (<a href="https://github.com/uchiha-fire">@uchiha-fire</a>) &bull; <a href="mailto:sharmashubham25962@gmail.com">sharmashubham25962@gmail.com</a></sub>
</p>
