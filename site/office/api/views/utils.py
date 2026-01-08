def get_language_style(self):
    return self.office.settings["language_style"]


def get_file_for_style(self, base_filename, style=None):
    if style is None:
        style = self.get_language_style()
    if style == "traditional":
        return f"{base_filename}_traditional"
    if style == "spanish":
        return f"{base_filename}_spanish"
    return base_filename


def get_text_for_style(self, item, style=None):
    if style is None:
        style = self.get_language_style()

    if style == "traditional":
        if isinstance(item, dict) and "traditional" in item:
            return item["traditional"]
        if hasattr(item, "traditional_text_no_tags"):
            return item.traditional_text_no_tags

    if style == "spanish":
        if isinstance(item, dict) and "spanish" in item:
            return item["spanish"]
        if hasattr(item, "spanish_text_no_tags"):
            return item.spanish_text_no_tags

    if isinstance(item, dict) and "contemporary" in item:
        return item["contemporary"]
    if hasattr(item, "text_no_tags"):
        return item.text_no_tags

    # Fallback for dictionaries that might use 'sentence' or numeric keys
    if isinstance(item, dict):
        if style == "traditional" and 1 in item:
            return item[1]
        if 0 in item:
            return item[0]
        if "sentence" in item:
            return item["sentence"]

    return str(item)
