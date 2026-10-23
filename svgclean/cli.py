"""
CLI interface and interactive wizard for svgclean.
Zephyrus Labs (https://zephyrus-labs.tech/)
Lead Developer: Shubham Sharma
"""
import argparse
import os
import sys
from typing import List, Optional

from svgclean import __version__
from svgclean.core import clean_svg, clean_file, clean_directory, SvgResult

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    banner = f"""{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║               svgclean-cli  v{__version__}                          ║
║     SVG Sanitizer, Minifier, & Security Scrubber             ║
║     Zephyrus Labs (https://zephyrus-labs.tech/)              ║
╚══════════════════════════════════════════════════════════════╝{RESET}"""
    print(banner)


def display_result_summary(result: SvgResult, label: str = "SVG File", dry_run: bool = False):
    tag = f"{YELLOW}[Dry-Run]{RESET} " if dry_run else ""
    print(f"\n{BOLD}{tag}Sanitization & Optimization Summary for {label}:{RESET}")
    print("-" * 65)
    print(f"  {BOLD}Original Size:{RESET}       {result.orig_bytes:,} bytes")
    print(f"  {BOLD}Cleaned Size:{RESET}        {result.final_bytes:,} bytes")
    print(f"  {BOLD}Bytes Saved:{RESET}         {GREEN}{result.saved_bytes:,} bytes ({result.saved_pct:.1f}% reduction){RESET}")
    print(f"  {BOLD}Threats Neutralized:{RESET} {RED if result.threats_count > 0 else GREEN}{result.threats_count}{RESET}")

    if result.threats_removed:
        print(f"\n  {BOLD}Neutralized Security Risks:{RESET}")
        for threat in result.threats_removed:
            print(f"    - {RED}{threat}{RESET}")
    print("-" * 65 + "\n")


def run_interactive_wizard() -> int:
    print_banner()
    print(f"\n{BOLD}Welcome to the svgclean Interactive Sanitizer Wizard!{RESET}\n")

    print(f"{BOLD}Select Source Type:{RESET}")
    print("  [1] Sanitize single SVG file")
    print("  [2] Batch sanitize a directory of SVG files")
    print("  [3] Paste inline raw SVG XML string")

    choice = input(f"{BOLD}Choose [1/2/3] (default: 1):{RESET} ").strip() or "1"

    if choice == "3":
        print(f"\n{BOLD}Paste SVG XML string below (end with an empty line):{RESET}")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        raw_xml = "\n".join(lines)
        if not raw_xml:
            print(f"{RED}No SVG content provided.{RESET}")
            return 1
        res = clean_svg(raw_xml)
        display_result_summary(res, label="Inline SVG")
        print(f"{BOLD}Cleaned SVG Output:{RESET}\n{res.cleaned_svg}\n")
        return 0

    if choice == "2":
        dir_path = input(f"{BOLD}Enter path to directory containing SVG files:{RESET} ").strip()
        if not dir_path or not os.path.exists(dir_path):
            print(f"{RED}Directory not found: '{dir_path}'{RESET}")
            return 1
        default_out = f"{dir_path.rstrip(os.sep)}_clean"
        out_dir = input(f"{BOLD}Enter output directory (default: {default_out}):{RESET} ").strip() or default_out
        prec_str = input(f"{BOLD}Coordinate decimal precision [0-4] (default: 2):{RESET} ").strip() or "2"
        precision = int(prec_str) if prec_str.isdigit() else 2

        print(f"\n{CYAN}Processing SVG directory...{RESET}")
        summary = clean_directory(dir_path, output_dir=out_dir, precision=precision)
        print(f"{GREEN}✓ Batch sanitization complete!{RESET}")
        print(f"  Files processed: {summary['files_processed']}")
        print(f"  Total threats neutralized: {summary['total_threats_neutralized']}")
        print(f"  Total bytes saved: {summary['total_saved_bytes']:,} bytes")
        print(f"  Clean files saved to: {out_dir}\n")
        return 0

    # Choice 1: Single file
    file_path = input(f"{BOLD}Enter path to SVG file:{RESET} ").strip()
    if not file_path or not os.path.exists(file_path):
        print(f"{RED}File not found: '{file_path}'{RESET}")
        return 1

    base, ext = os.path.splitext(file_path)
    default_out = f"{base}_clean{ext}"
    out_path = input(f"{BOLD}Enter output file path (default: {default_out}):{RESET} ").strip() or default_out

    prec_str = input(f"{BOLD}Coordinate decimal precision [0-4] (default: 2):{RESET} ").strip() or "2"
    precision = int(prec_str) if prec_str.isdigit() else 2

    strip_scripts_str = input(f"{BOLD}Strip <script> tags and event handlers? [Y/n]:{RESET} ").strip().lower()
    strip_scripts = strip_scripts_str != "n"

    rem_meta_str = input(f"{BOLD}Remove editor metadata and namespaces? [Y/n]:{RESET} ").strip().lower()
    rem_meta = rem_meta_str != "n"

    dry_run_str = input(f"{BOLD}Dry-run only (do not write output file)? [y/N]:{RESET} ").strip().lower()
    dry_run = dry_run_str == "y"

    try:
        if dry_run:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                res = clean_svg(f.read(), precision=precision, strip_scripts=strip_scripts, remove_metadata=rem_meta)
        else:
            res = clean_file(file_path, output_path=out_path, precision=precision, strip_scripts=strip_scripts, remove_metadata=rem_meta)

        display_result_summary(res, label=os.path.basename(file_path), dry_run=dry_run)
        if not dry_run:
            print(f"{GREEN}✓ Sanitized SVG saved cleanly to: {out_path}{RESET}\n")
        return 0
    except Exception as e:
        print(f"{RED}Error processing SVG: {e}{RESET}")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv or "--interactive" in argv or "-i" in argv:
        return run_interactive_wizard()

    parser = argparse.ArgumentParser(
        prog="svgclean",
        description="SVG Sanitizer, Minifier, & Security Scrubber by Zephyrus Labs",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Input SVG file or directory of SVGs",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output path for cleaned SVG file or output directory",
    )
    parser.add_argument(
        "-p",
        "--precision",
        type=int,
        default=2,
        help="Number of decimal digits for coordinate precision (default: 2)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Report threats and byte savings without saving files",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite destination files without prompt",
    )
    parser.add_argument(
        "--keep-metadata",
        action="store_true",
        help="Retain editor metadata and descriptions",
    )
    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="Suppress banner and non-essential progress output",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Launch interactive sanitizer wizard",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"svgclean-cli {__version__} by Zephyrus Labs",
    )

    args = parser.parse_args(argv)

    if not args.input:
        return run_interactive_wizard()

    target = args.input
    if not os.path.exists(target):
        print(f"{RED}Error: Input path '{target}' does not exist.{RESET}", file=sys.stderr)
        return 1

    remove_metadata = not args.keep_metadata

    # Directory batch
    if os.path.isdir(target):
        out_dir = args.output
        if not out_dir and not args.dry_run:
            out_dir = f"{target.rstrip(os.sep)}_clean"
        try:
            summary = clean_directory(
                target,
                output_dir=None if args.dry_run else out_dir,
                precision=args.precision,
                remove_metadata=remove_metadata,
            )
            if not args.silent:
                print(f"{GREEN}✓ Batch sanitization complete for '{target}'!{RESET}")
                print(f"  Files processed:           {summary['files_processed']}")
                print(f"  Threats neutralized:       {summary['total_threats_neutralized']}")
                print(f"  Bytes saved:               {summary['total_saved_bytes']:,} bytes")
                if not args.dry_run:
                    print(f"  Output directory:          {out_dir}")
            return 0
        except Exception as e:
            print(f"{RED}Error during batch processing: {e}{RESET}", file=sys.stderr)
            return 1

    # Single file
    out_file = args.output
    if not out_file and not args.dry_run:
        base, ext = os.path.splitext(target)
        out_file = f"{base}_clean{ext}"

    if out_file and os.path.exists(out_file) and not args.force and not args.dry_run:
        print(f"{RED}Error: Output file '{out_file}' already exists. Use -f/--force to overwrite.{RESET}", file=sys.stderr)
        return 1

    try:
        if args.dry_run:
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                res = clean_svg(f.read(), precision=args.precision, remove_metadata=remove_metadata)
        else:
            res = clean_file(target, output_path=out_file, precision=args.precision, remove_metadata=remove_metadata)

        if not args.silent:
            display_result_summary(res, label=os.path.basename(target), dry_run=args.dry_run)
            if not args.dry_run:
                print(f"{GREEN}✓ Cleaned SVG saved to: {out_file}{RESET}")
        return 0
    except Exception as e:
        print(f"{RED}Error cleaning SVG: {e}{RESET}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
