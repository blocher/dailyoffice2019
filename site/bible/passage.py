from bible.sources import BibleGateway, OremusBibleBrowser, BCPPsalter, get_esv_xml_adapter


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
        "av": {"name": "King James Version", "adapter": OremusBibleBrowser},
        "coverdale": {"name": "Coverdale Psalter (1928)", "adapter": BCPPsalter},
        "renewed_coverdale": {"name": "Renewed Coverdale Psalter (2019)", "adapter": BCPPsalter},
    }


class Passage(object):
    def __init__(self, passage, source="nrsv"):
        source = source.lower()
        version = BibleVersions.VERSIONS.get(source, {"name": source, "adapter": BibleGateway})
        adapter = version["adapter"]
        
        # Handle lazy-loaded adapters (like ESV XML)
        if callable(adapter):
            adapter_class = adapter()
        else:
            adapter_class = adapter
        
        self.lookup = adapter_class(passage, source)
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
