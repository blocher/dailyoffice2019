from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from office.utils import generate_uuid_from_string


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


class Module(object):
    def __init__(self, office=None):
        self.office = office

    def get_name(self):
        if hasattr(self, "name"):
            return self.name
        return "Daily Office Module"

    def get_safe_name(self):
        return "".join(filter(str.isalpha, self.get_name().replace(" ", "_").lower()))

    def strip_line(self, line):
        line["content"] = line["content"].strip()
        line["line_type"] = line["line_type"].strip()
        return line

    def get_formatted_lines(self):
        i = 0
        lines = self.get_lines()
        if not lines:
            return lines
        lines = [self.strip_line(line) for line in lines]
        lines = [
            line
            for line in lines
            if line and (line.get("content") or (line.get("line_type") and line["line_type"] == "spacer"))
        ]
        lines = [self.mark_html_safe(line) for line in lines]
        for line in lines:
            line["audio_id"] = generate_uuid_from_string(line["content"])
            line["id"] = f"{self.get_safe_name()}_{i}_{line['audio_id']}"
            i = i + 1
        return lines

    def get_lines(self):
        raise NotImplementedError("You must implement this method.")

    @staticmethod
    def mark_html_safe(line):
        if not isinstance(line, dict):
            return line
        if line.get("line_type") == "html":
            line["content"] = mark_safe(line["content"])
        return line

    @cached_property
    def json(self):
        lines = self.get_formatted_lines()
        return {"name": self.get_name(), "lines": lines}
