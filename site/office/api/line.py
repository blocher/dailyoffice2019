"""Shared Line class and file_to_lines utility.

Extracted to break circular imports between office.api.views, office.api.views.index, and psalter.utils.
"""
import csv
import os
from distutils.util import strtobool

from office.api.translations import get_csv_suffix, is_chinese


class Line(dict):
    def __init__(
        self,
        content,
        line_type="congregation",
        indented=False,
        preface=None,
        extra_space_before=False,
        audio_heading_content=None,
        *args,
        **kwargs,
    ):
        super().__init__(
            content=content,
            line_type=line_type,
            indented=indented,
            preface=preface,
            extra_space_before=extra_space_before,
            audio_heading_content=audio_heading_content,
            *args,
            **kwargs,
        )


def file_to_lines(filename, language="english"):
    def process_row(row):
        result = {"content": row[0]}
        if len(row) > 1 and row[1]:
            result["line_type"] = row[1]
        result["indented"] = False
        if len(row) > 2:
            if row[2].lower() == "true":
                result["indented"] = "indent"
            else:
                result["indented"] = row[2]

        if len(row) > 3:
            if not row[3]:
                result["extra_space_before"] = False
            else:
                result["extra_space_before"] = bool(strtobool(row[3].lower()))
        return result

    base_filename = filename.replace(".csv", "")
    suffix = get_csv_suffix(language)
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "texts")

    # Build list of filenames to try, in priority order
    candidates = []
    if suffix:
        candidates.append("{}{}.csv".format(base_filename, suffix))
        if is_chinese(language) and "_traditional" in base_filename:
            stripped = base_filename.replace("_traditional", "")
            candidates.append("{}{}.csv".format(stripped, suffix))
    candidates.append("{}.csv".format(base_filename))

    for try_filename in candidates:
        filepath = os.path.join(dir_path, try_filename)
        if os.path.exists(filepath):
            with open(filepath, encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, quotechar='"', delimiter=",", quoting=csv.QUOTE_ALL, skipinitialspace=True)
                return [Line(**process_row(row)) for row in reader]
