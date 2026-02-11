#!/usr/bin/env python3
"""
JSON Beautifier - Replaces newlines in JSON string values with spaces.

Usage:
    python beautifier.py <path_to_json_file_or_folder>
"""

import json
import re
import sys
from pathlib import Path


def fix_newlines(obj):
    """Recursively replace newlines with spaces in all string values."""
    if isinstance(obj, str):
        # Replace actual newlines with a space, then collapse multiple spaces
        return re.sub(r'\s+', ' ', obj.replace('\n', ' ')).strip()
    elif isinstance(obj, dict):
        return {k: fix_newlines(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_newlines(item) for item in obj]
    return obj


def beautify_json_file(filepath: Path):
    """Read, fix, and overwrite a JSON file with proper newlines."""
    print(f"Processing: {filepath}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    fixed_data = fix_newlines(data)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(fixed_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Done")


def main():
    if len(sys.argv) != 2:
        print("Usage: python beautifier.py <path_to_json_file_or_folder>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    
    if not path.exists():
        print(f"Error: Path '{path}' does not exist.")
        sys.exit(1)
    
    if path.is_file():
        if path.suffix.lower() == ".json":
            beautify_json_file(path)
        else:
            print(f"Error: '{path}' is not a .json file.")
            sys.exit(1)
    
    elif path.is_dir():
        json_files = list(path.glob("*.json"))
        if not json_files:
            print(f"No .json files found in '{path}'")
            sys.exit(1)
        
        print(f"Found {len(json_files)} JSON file(s)\n")
        for json_file in json_files:
            beautify_json_file(json_file)
        print(f"\n✓ All done! Processed {len(json_files)} file(s).")
    
    else:
        print(f"Error: '{path}' is neither a file nor a directory.")
        sys.exit(1)


if __name__ == "__main__":
    main()