"""Sorts the list items in a markdown file in-place."""

import re
import sys
from pathlib import Path


def sort_markdown_list(file_path: str) -> None:
    """Sorts the list items in a markdown file in-place."""
    with Path(file_path).open() as file:
        lines = file.readlines()

    sorted_lines = []
    in_list = False
    list_block = []

    for line in lines:
        # Detect list items (unordered or ordered)
        if re.match(r"^\s*[-*+]\s", line) or re.match(r"^\s*\d+\.\s", line):
            list_block.append(line)
            in_list = True
        else:
            if in_list:
                sorted_lines += sorted(
                    list_block,
                    key=lambda x: x.lower(),
                )  # Sort ignoring case
                list_block = []
            sorted_lines.append(line)
            in_list = False

    if list_block:
        sorted_lines += sorted(list_block, key=lambda x: x.lower())

    # Write the sorted content back to the file
    with Path(file_path).open("w") as file:
        file.writelines(sorted_lines)


if __name__ == "__main__":
    for markdown_file in sys.argv[1:]:
        sort_markdown_list(markdown_file)
