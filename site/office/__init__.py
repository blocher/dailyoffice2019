# ==== Sections


class OfficeSection(object):
    def render(self):
        raise NotImplementedError


class TestSection(OfficeSection):
    def render(self):

        print("test")


# ==== Offices


class Office(object):

    name = "Daily Office"
    modules = []

    def render(self):
        for module in self.modules:
            module = module()
            module.render()


class EveningPrayer(Office):

    name = "Evening Prayer"
    modules = [TestSection]
