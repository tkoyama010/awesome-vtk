#!/usr/bin/env python3
import sys
import re


def sort_markdown_list(file_path):
    with open(file_path, "r") as file:
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
                    list_block, key=lambda x: x.lower()
                )  # Sort ignoring case
                list_block = []
            sorted_lines.append(line)
            in_list = False

    if list_block:
        sorted_lines += sorted(list_block, key=lambda x: x.lower())

    # Write the sorted content back to the file
    with open(file_path, "w") as file:
        file.writelines(sorted_lines)


if __name__ == "__main__":
    for markdown_file in sys.argv[1:]:
        sort_markdown_list(markdown_file)
