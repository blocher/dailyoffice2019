from bible.sources import BibleGateway, OremusBibleBrowser, BCPPsalter, get_esv_xml_adapter
from bible.ccreadbible_adapter import CCReadBible


class BibleVersions(object):
    VERSIONS = {
        "nrsvce": {"name": "New Revised Standard Version", "adapter": BibleGateway},
        "esv": {"name": "English Standard Version", "adapter": BibleGateway},
        "esv_xml": {"name": "English Standard Version (XML)", "adapter": get_esv_xml_adapter},
        "rsv": {"name": "Revised Standard Version", "adapter": BibleGateway},
        "kjv": {"name": "King James Version", "adapter": BibleGateway},
        "nabre": {"name": "New American Bible - Revised Edition", "adapter": BibleGateway},
        "niv": {"name": "New International Version", "adapter": BibleGateway},
        "nasb": {"name": "New American Standard Bible", "adapter": BibleGateway},
        "cuvs": {"name": "Chinese Union Version (Simplified)", "adapter": BibleGateway},
        "cuv": {"name": "Chinese Union Version (Traditional)", "adapter": BibleGateway},
        "sigao": {"name": "Studium Biblicum O.F.M. (Traditional)", "adapter": CCReadBible},
        "znsigao": {"name": "Studium Biblicum O.F.M. (Simplified)", "adapter": CCReadBible},
        "nvi": {"name": "Nueva Versión Internacional", "adapter": BibleGateway},
        "rv1960": {"name": "Reina-Valera 1960", "adapter": BibleGateway},
        "av": {"name": "King James Version", "adapter": OremusBibleBrowser},
        "coverdale": {"name": "Coverdale Psalter (1928)", "adapter": BCPPsalter},
        "renewed_coverdale": {"name": "Renewed Coverdale Psalter (2019)", "adapter": BCPPsalter},
    }


class Passage(object):
    def __init__(self, passage, source="nrsv"):
        source = source.lower()
        version = BibleVersions.VERSIONS.get(source, {"name": source, "adapter": BibleGateway})
        adapter = version["adapter"]

        # Handle lazy-loaded adapters (like ESV XML) - functions that return a class
        import inspect
        if callable(adapter) and not inspect.isclass(adapter):
            adapter = adapter()

        self.lookup = adapter(passage, source)
        self.version_abbreviation = source
        self.version_name = version["name"]

    @property
    def text(self):
        return self.lookup.get_text()

    @property
    def html(self):
        return self.lookup.get_html()

    @property
    def headings(self):
        return self.lookup.get_headings()
