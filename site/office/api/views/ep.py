from office.api.views import Module, Line


class EPOpeningSentence(Module):
    name = "Opening Sentence"

    def get_sentence(self):
        if "Thanksgiving Day" in self.office.date.primary_evening.name:
            return {
                "sentence": "The Lord by wisdom founded the earth; by understanding he established the heavens; by his knowledge the deeps broke open, and the clouds drop down the dew.",
                "traditional": "The Lord by wisdom hath founded the earth; by understanding hath he established the heavens. By his knowledge the depths are broken up, and the clouds drop down the dew.",
                "citation": "PROVERBS 3:19-20",
            }

        if self.office.date.evening_season.name == "Holy Week":
            return {
                "sentence": "All we like sheep have gone astray; we have turned every one to his own way; and the Lord has laid on him the iniquity of us all.",
                "traditional": "All we like sheep have gone astray; we have turned every one to his own way; and the Lord hath laid on him the iniquity of us all. ",
                "citation": "ISAIAH 53:6",
            }

        if (
            self.office.date.evening_season.name == "Lent"
            or self.office.date.primary_evening.rank.name == "EMBER_DAY"
            or self.office.date.primary_evening.rank.name == "ROGATION_DAY"
        ):
            if self.office.date.date.weekday() in [6, 2]:  # Sunday, Wednesday
                return {
                    "sentence": "To the Lord our God belong mercy and forgiveness, for we have rebelled against him.",
                    "traditional": "To the Lord our God belong mercies and forgivenesses, though we have rebelled against him.",
                    "citation": "DANIEL 9:9",
                }

            if self.office.date.date.weekday() in [0, 3, 5]:  # Monday, Thursday, Saturday
                return {
                    "sentence": "For I acknowledge my faults, and my sin is ever before me.",
                    "traditional": "I acknowledge my transgressions: and my sin is ever before me.",
                    "citation": "PSALM 51:3",
                }

            return {  # Tuesday, Friday
                "sentence": "If we say we have no sin, we deceive ourselves, and the truth is not in us. If we confess our sins, he is faithful and just to forgive us our sins and to cleanse us from all unrighteousness.",
                "traditional": "If we say that we have no sin, we deceive ourselves, and the truth is not in us; but if we confess our sins, God is faithful and just to forgive us our sins, and to cleanse us from all unrighteousness.",
                "citation": "1 JOHN 1:8-9",
            }

        if self.office.date.evening_season.name == "Advent":
            return {
                "sentence": "Therefore stay awake—for you do not know when the master of the house will come, in the evening, or at midnight, or when the rooster crows, or in the morning—lest he come suddenly and find you asleep.",
                "traditional": "Watch ye therefore: for ye know not when the master of the house cometh, at even, or at midnight, or at the cock-crowing, or in the morning: Lest coming suddenly he find you sleeping.",
                "citation": "MARK 13:35-36",
            }

        if self.office.date.evening_season.name == "Christmastide":
            return {
                "sentence": "Behold, the dwelling place of God is with man. He will dwell with them, and they will be his people, and God himself will be with them as their God.",
                "traditional": "Behold, the tabernacle of God is with men, and he will dwell with them, and they shall be his people, and God himself shall be with them, and be their God.",
                "citation": "REVELATION 21:3",
            }

        if self.office.date.evening_season.name == "Epiphanytide":
            return {
                "sentence": "Nations shall come to your light, and kings to the brightness of your rising.",
                "traditional": "And the Gentiles shall come to thy light, and kings to the brightness of thy rising.",
                "citation": "ISAIAH 60:3",
            }

        if (
            self.office.date.primary_evening.name == "The Day of Pentecost"
            or self.office.date.primary_evening.name == "Eve of The Day of Pentecost"
        ):
            if self.office.date.date.year % 2 == 0:
                return {
                    "sentence": "The Spirit and the Bride say, “Come.” And let the one who hears say, “Come.” And let the one who is thirsty come; let the one who desires take the water of life without price.",
                    "traditional": "The Spirit and the bride say, Come. And let him that heareth say, Come. And let him that is athirst come. And whosoever will, let him take the water of life freely.",
                    "citation": "REVELATION 22:17",
                }

            return {
                "sentence": "There is a river whose streams make glad the city of God, the holy dwelling place of the Most High.",
                "traditional": "There is a river, the streams whereof shall make glad the city of God, the holy place of the tabernacle of the Most High.",
                "citation": "PSALM 46:4",
            }

        if (
            "Ascension" in self.office.date.primary_evening.name
            or len(self.office.date.all_evening) > 1
            and "Ascension" in self.office.date.all_evening[1].name
        ):
            return {
                "sentence": "For Christ has entered, not into holy places made with hands, which are copies of the true things, but into heaven itself, now to appear in the presence of God on our behalf.",
                "traditional": "Christ is not entered into the holy places made with hands, which are the figures of the true; but into heaven itself, now to appear in the presence of God for us.",
                "citation": "HEBREWS 9:24",
            }

        if (
            self.office.date.primary_evening.name == "Trinity Sunday"
            or self.office.date.primary_evening.name == "Eve of Trinity Sunday"
        ):
            return {
                "sentence": "Holy, holy, holy is the Lord of Hosts; the whole earth is full of his glory!",
                "traditional": "Holy, holy, holy is the Lord of Hosts: the whole earth is full of his glory.",
                "citation": "ISAIAH 6:3",
            }

        if self.office.date.evening_season.name == "Eastertide":
            return {
                "sentence": "Thanks be to God, who gives us the victory through our Lord Jesus Christ.",
                "traditional": "Thanks be to God, which giveth us the victory through our Lord Jesus Christ.",
                "citation": "1 CORINTHIANS 15:57",
            }

        if self.office.date.date.weekday() == 0 or self.office.date.date.weekday() == 5:
            return {
                "sentence": "Jesus spoke to them, saying, “I am the light of the world. Whoever follows me will not walk in darkness, but will have the light of life.”",
                "traditional": "Then spake Jesus again unto them, saying, I am the light of the world: he that followeth me shall not walk in darkness, but shall have the light of life.",
                "citation": "JOHN 8:12",
            }

        if self.office.date.date.weekday() == 1 or self.office.date.date.weekday() == 6:
            return {
                "sentence": "Lord, I have loved the habitation of your house and the place where your honor dwells.",
                "traditional": "Lord, I have loved the habitation of thy house, and the place where thine honor dwelleth.",
                "citation": "PSALM 26:8",
            }

        if self.office.date.date.weekday() == 2:
            return {
                "sentence": "Let my prayer be set forth in your sight as incense, and let the lifting up of my hands be an evening sacrifice.",
                "traditional": "Let my prayer be set forth in thy sight as the incense; and let the lifting up of my hands be an evening sacrifice.",
                "citation": "PSALM 141:2",
            }

        if self.office.date.date.weekday() == 3:
            return {
                "sentence": "O worship the Lord in the beauty of holiness; let the whole earth stand in awe of him.",
                "traditional": "O worship the Lord in the beauty of holiness; let the whole earth stand in awe of him.",
                "citation": "PSALM 96:9",
            }

        if self.office.date.date.weekday() == 4:
            return {
                "sentence": "I will thank the Lord for giving me counsel; my heart also chastens me in the night season. I have set the Lord always before me; he is at my right hand, therefore I shall not fall.",
                "traditional": "I will thank the Lord for giving me warning, my reins also chasten me in the night season. I have set the Lord alway before me; for he is on my right hand, therefore I shall not fall.",
                "citation": "PSALM 16:8-9",
            }

    def get_lines(self):
        sentence = self.get_sentence()
        style = self.office.settings["language_style"]
        return [
            Line("Opening Sentence", "heading"),
            Line(sentence["traditional"] if style == "traditional" else sentence["sentence"], "leader"),
            Line(sentence["citation"], "citation"),
        ]
