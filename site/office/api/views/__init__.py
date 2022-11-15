from django.utils.functional import cached_property
from django.utils.safestring import mark_safe


class Line(dict):
    def __init__(
        self,
        content,
        line_type="congregation",
        indented=False,
        preface=None,
        extra_space_before=False,
        *args,
        **kwargs,
    ):
        super().__init__(
            content=content,
            line_type=line_type,
            indented=indented,
            preface=preface,
            extra_space_before=extra_space_before,
            *args,
            **kwargs,
        )


class Module(object):
    def __init__(self, office):
        self.office = office

    def get_name(self):
        if hasattr(self, "name"):
            return self.name
        return "Daily Office Module"

    def strip_line(self, line):
        line["content"] = line["content"].strip()
        line["line_type"] = line["line_type"].strip()
        return line

    def get_formatted_lines(self):
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
