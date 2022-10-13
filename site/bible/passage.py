from bible.sources import BibleGateway, OremusBibleBrowser, BCPPsalter


class BibleVersions(object):
    VERSIONS = {
        "nrsvce": {"name": "New Revised Standard Version", "adapter": BibleGateway},
        "esv": {"name": "English Standard Version", "adapter": BibleGateway},
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
        if source not in BibleVersions.VERSIONS.keys():
            raise Exception(f"This bible format ({source}) is not currently supported")
        adapter = BibleVersions.VERSIONS[source]["adapter"]
        self.lookup = adapter(passage, source)

    @property
    def text(self):
        return self.lookup.get_text()

    @property
    def html(self):
        return self.lookup.get_html()

    @property
    def headings(self):
        return self.lookup.get_headings()
