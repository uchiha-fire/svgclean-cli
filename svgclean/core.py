"""
Core SVG sanitization and minification engine.
Zephyrus Labs (https://zephyrus-labs.tech/)
Lead Developer: Shubham Sharma
"""
import os
import re
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as standard_ET
import defusedxml.ElementTree as ET

BLACK_LIST_TAGS = {
    "script",
    "foreignobject",
    "applet",
    "object",
    "iframe",
    "embed",
}

# Register standard SVG namespaces so serializer doesn't generate ns0: prefixes
standard_ET.register_namespace("", "http://www.w3.org/2000/svg")
standard_ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

EVENT_ATTR_REGEX = re.compile(r"^on[a-z]+", re.IGNORECASE)
FLOAT_REGEX = re.compile(r"\b\d+\.\d{3,}\b")


class SvgResult:
    """Encapsulates the result of SVG sanitization and minification."""
    def __init__(
        self,
        cleaned_svg: str,
        threats_removed: List[str],
        orig_bytes: int,
        final_bytes: int,
    ):
        self.cleaned_svg = cleaned_svg
        self.threats_removed = threats_removed
        self.orig_bytes = orig_bytes
        self.final_bytes = final_bytes

    @property
    def saved_bytes(self) -> int:
        return max(0, self.orig_bytes - self.final_bytes)

    @property
    def saved_pct(self) -> float:
        if self.orig_bytes == 0:
            return 0.0
        return (self.saved_bytes / self.orig_bytes) * 100.0

    @property
    def threats_count(self) -> int:
        return len(self.threats_removed)


def clean_svg(
    svg_content: str,
    precision: int = 2,
    strip_scripts: bool = True,
    remove_metadata: bool = True,
) -> SvgResult:
    """
    Sanitizes and minifies an SVG XML string.
    """
    orig_bytes = len(svg_content.encode("utf-8"))
    threats: List[str] = []

    # Parse with defusedxml to prevent entity bombs (Billion Laughs / XXE)
    root = ET.fromstring(svg_content)

    # Build parent map to facilitate clean removal of blacklisted child elements
    parent_map = {c: p for p in root.iter() for c in p}

    # 1. Strip blacklisted elements and editor bloat
    for elem in list(root.iter()):
        tag_name = elem.tag.split("}")[-1].lower()

        # Security element blacklist
        if strip_scripts and tag_name in BLACK_LIST_TAGS:
            threats.append(f"Removed unsafe element: <{tag_name}>")
            parent = parent_map.get(elem)
            if parent is not None:
                parent.remove(elem)
            continue

        # Editor metadata and namespaces
        if remove_metadata:
            if tag_name in ("metadata", "desc") or any(ns in elem.tag.lower() for ns in ("inkscape", "sodipodi", "adobe", "sketch")):
                parent = parent_map.get(elem)
                if parent is not None:
                    parent.remove(elem)
                continue

        # 2. Strip event handlers and malicious URIs
        for attr in list(elem.attrib.keys()):
            attr_local = attr.split("}")[-1].lower()
            if EVENT_ATTR_REGEX.match(attr_local) or EVENT_ATTR_REGEX.match(attr):
                threats.append(f"Removed inline event handler: {attr}")
                del elem.attrib[attr]
                continue

            val = str(elem.attrib.get(attr, "")).strip().lower()
            if any(val.startswith(proto) for proto in ("javascript:", "vbscript:", "data:text/html")):
                threats.append(f"Neutralized malicious URI in {attr}")
                del elem.attrib[attr]
                continue

            if remove_metadata and any(ns in attr.lower() for ns in ("inkscape:", "sodipodi:", "adobe:")):
                del elem.attrib[attr]

    # 3. Prune empty <g> groups
    for elem in list(root.iter()):
        tag_name = elem.tag.split("}")[-1].lower()
        if tag_name == "g" and len(elem) == 0:
            parent = parent_map.get(elem)
            if parent is not None:
                parent.remove(elem)

    # 4. Serialize back to XML
    clean_xml = standard_ET.tostring(root, encoding="unicode")

    # 5. Coordinate precision limiting
    if precision is not None and precision >= 0:
        def round_float(match):
            val = float(match.group(0))
            rounded = f"{val:.{precision}f}"
            if "." in rounded:
                rounded = rounded.rstrip("0").rstrip(".")
            return rounded

        clean_xml = FLOAT_REGEX.sub(round_float, clean_xml)

    final_bytes = len(clean_xml.encode("utf-8"))

    return SvgResult(
        cleaned_svg=clean_xml,
        threats_removed=threats,
        orig_bytes=orig_bytes,
        final_bytes=final_bytes,
    )


def clean_file(
    input_path: str,
    output_path: Optional[str] = None,
    precision: int = 2,
    strip_scripts: bool = True,
    remove_metadata: bool = True,
) -> SvgResult:
    """Sanitizes an SVG file and writes the clean version."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    result = clean_svg(
        content,
        precision=precision,
        strip_scripts=strip_scripts,
        remove_metadata=remove_metadata,
    )

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result.cleaned_svg)

    return result


def clean_directory(
    dir_path: str,
    output_dir: Optional[str] = None,
    precision: int = 2,
    strip_scripts: bool = True,
    remove_metadata: bool = True,
) -> Dict[str, Any]:
    """Batch sanitizes all SVG files within a directory."""
    if not os.path.exists(dir_path):
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    files_processed = 0
    total_orig = 0
    total_final = 0
    total_threats = 0

    for root, _, files in os.walk(dir_path):
        for f in files:
            if f.lower().endswith(".svg"):
                full_in = os.path.join(root, f)
                if output_dir:
                    rel = os.path.relpath(full_in, dir_path)
                    full_out = os.path.join(output_dir, rel)
                else:
                    full_out = None

                res = clean_file(
                    full_in,
                    full_out,
                    precision=precision,
                    strip_scripts=strip_scripts,
                    remove_metadata=remove_metadata,
                )
                files_processed += 1
                total_orig += res.orig_bytes
                total_final += res.final_bytes
                total_threats += res.threats_count

    return {
        "files_processed": files_processed,
        "total_orig_bytes": total_orig,
        "total_final_bytes": total_final,
        "total_saved_bytes": max(0, total_orig - total_final),
        "total_threats_neutralized": total_threats,
    }
