import re

import scriptures
from num2words import num2words

# Mapping from English book names to Spanish book names
english_to_spanish = {
    "Genesis": "Génesis",
    "Exodus": "Éxodo",
    "Leviticus": "Levítico",
    "Numbers": "Números",
    "Deuteronomy": "Deuteronomio",
    "Joshua": "Josué",
    "Judges": "Jueces",
    "Ruth": "Rut",
    "I Samuel": "I Samuel",
    "II Samuel": "II Samuel",
    "I Kings": "I Reyes",
    "II Kings": "II Reyes",
    "I Chronicles": "I Crónicas",
    "II Chronicles": "II Crónicas",
    "Ezra": "Esdras",
    "Nehemiah": "Nehemías",
    "Esther": "Ester",
    "Job": "Job",
    "Psalms": "Salmos",
    "Proverbs": "Proverbios",
    "Ecclesiastes": "Eclesiastés",
    "Song of Songs": "Cantar de los Cantares",
    "Isaiah": "Isaías",
    "Jeremiah": "Jeremías",
    "Lamentations": "Lamentaciones",
    "Ezekiel": "Ezequiel",
    "Daniel": "Daniel",
    "Hosea": "Oseas",
    "Joel": "Joel",
    "Amos": "Amós",
    "Obadiah": "Abdías",
    "Jonah": "Jonás",
    "Micah": "Miqueas",
    "Nahum": "Nahúm",
    "Habakkuk": "Habacuc",
    "Zephaniah": "Sofonías",
    "Haggai": "Hageo",
    "Zechariah": "Zacarías",
    "Malachi": "Malaquías",
    "Matthew": "Mateo",
    "Mark": "Marcos",
    "Luke": "Lucas",
    "John": "Juan",
    "Acts": "Hechos",
    "Romans": "Romanos",
    "I Corinthians": "I Corintios",
    "II Corinthians": "II Corintios",
    "Galatians": "Gálatas",
    "Ephesians": "Efesios",
    "Philippians": "Filipenses",
    "Colossians": "Colosenses",
    "I Thessalonians": "I Tesalonicenses",
    "II Thessalonians": "II Tesalonicenses",
    "I Timothy": "I Timoteo",
    "II Timothy": "II Timoteo",
    "Titus": "Tito",
    "Philemon": "Filemón",
    "Hebrews": "Hebreos",
    "James": "Santiago",
    "I Peter": "I Pedro",
    "II Peter": "II Pedro",
    "I John": "I Juan",
    "II John": "II Juan",
    "III John": "III Juan",
    "Jude": "Judas",
    "Revelation": "Apocalipsis",
    "Tobit": "Tobías",
    "Judith": "Judit",
    "Additions to Esther": "Adiciones a Ester",
    "Wisdom": "Sabiduría",
    "Sirach": "Eclesiástico",
    "Baruch": "Baruc",
    "Letter of Jeremiah": "Carta de Jeremías",
    "Prayer of Azariah": "Oración de Azarías",
    "Susanna": "Susana",
    "Bel and the Dragon": "Bel y el Dragón",
    "I Maccabees": "I Macabeos",
    "II Maccabees": "II Macabeos",
    "I Esdras": "I Esdras",
    "II Esdras": "II Esdras",
    "Prayer of Manasseh": "Oración de Manasés",
}

# Spanish book names with long-form liturgical names (parallel to English 'books' variable)
spanish_books = {
    "Génesis": ("el Libro del Génesis", False, "OT"),
    "Éxodo": ("el Libro del Éxodo", False, "OT"),
    "Levítico": ("el Libro del Levítico", False, "OT"),
    "Números": ("el Libro de los Números", False, "OT"),
    "Deuteronomio": ("el Libro del Deuteronomio", False, "OT"),
    "Josué": ("el Libro de Josué", False, "OT"),
    "Jueces": ("el Libro de los Jueces", False, "OT"),
    "Rut": ("el Libro de Rut", False, "OT"),
    "I Samuel": ("el Primer Libro de Samuel", False, "OT"),
    "II Samuel": ("el Segundo Libro de Samuel", False, "OT"),
    "I Reyes": ("el Primer Libro de los Reyes", False, "OT"),
    "II Reyes": ("el Segundo Libro de los Reyes", False, "OT"),
    "I Crónicas": ("el Primer Libro de las Crónicas", False, "OT"),
    "II Crónicas": ("el Segundo Libro de las Crónicas", False, "OT"),
    "Esdras": ("el Libro de Esdras", False, "OT"),
    "Nehemías": ("el Libro de Nehemías", False, "OT"),
    "Ester": ("el Libro de Ester", False, "OT"),
    "Job": ("el Libro de Job", False, "OT"),
    "Salmos": ("los Salmos", False, "OT"),
    "Proverbios": ("los Proverbios", False, "OT"),
    "Eclesiastés": ("el Libro del Eclesiastés", False, "OT"),
    "Cantar de los Cantares": ("el Cantar de los Cantares", False, "OT"),
    "Isaías": ("el Profeta Isaías", False, "OT"),
    "Jeremías": ("el Libro de Jeremías", False, "OT"),
    "Lamentaciones": ("las Lamentaciones de Jeremías", False, "OT"),
    "Ezequiel": ("el Profeta Ezequiel", False, "OT"),
    "Daniel": ("el Profeta Daniel", False, "OT"),
    "Oseas": ("el Profeta Oseas", False, "OT"),
    "Joel": ("el Profeta Joel", False, "OT"),
    "Amós": ("el Profeta Amós", False, "OT"),
    "Abdías": ("el Profeta Abdías", True, "OT"),
    "Jonás": ("el Profeta Jonás", False, "OT"),
    "Miqueas": ("el Profeta Miqueas", False, "OT"),
    "Nahúm": ("el Profeta Nahúm", False, "OT"),
    "Habacuc": ("el Profeta Habacuc", False, "OT"),
    "Sofonías": ("el Profeta Sofonías", False, "OT"),
    "Hageo": ("el Profeta Hageo", False, "OT"),
    "Zacarías": ("el Profeta Zacarías", False, "OT"),
    "Malaquías": ("el Profeta Malaquías", False, "OT"),
    "Mateo": ("el Santo Evangelio de Nuestro Señor Jesucristo según San Mateo", False, "NT"),
    "Marcos": ("el Santo Evangelio de Nuestro Señor Jesucristo según San Marcos", False, "NT"),
    "Lucas": ("el Santo Evangelio de Nuestro Señor Jesucristo según San Lucas", False, "NT"),
    "Juan": ("el Santo Evangelio de Nuestro Señor Jesucristo según San Juan", False, "NT"),
    "Hechos": ("los Hechos de los Apóstoles", False, "NT"),
    "Romanos": ("la Epístola de San Pablo a los Romanos", False, "NT"),
    "I Corintios": ("la Primera Epístola de San Pablo a los Corintios", False, "NT"),
    "II Corintios": ("la Segunda Epístola de San Pablo a los Corintios", False, "NT"),
    "Gálatas": ("la Epístola de San Pablo a los Gálatas", False, "NT"),
    "Efesios": ("la Epístola de San Pablo a los Efesios", False, "NT"),
    "Filipenses": ("la Epístola de San Pablo a los Filipenses", False, "NT"),
    "Colosenses": ("la Epístola de San Pablo a los Colosenses", False, "NT"),
    "I Tesalonicenses": ("la Primera Epístola de San Pablo a los Tesalonicenses", False, "NT"),
    "II Tesalonicenses": ("la Segunda Epístola de San Pablo a los Tesalonicenses", False, "NT"),
    "I Timoteo": ("la Primera Epístola de San Pablo a San Timoteo", False, "NT"),
    "II Timoteo": ("la Segunda Epístola de San Pablo a San Timoteo", False, "NT"),
    "Tito": ("la Epístola de San Pablo a San Tito", False, "NT"),
    "Filemón": ("la Epístola de San Pablo a Filemón", True, "NT"),
    "Hebreos": ("la Epístola a los Hebreos", False, "NT"),
    "Santiago": ("la Epístola de Santiago", False, "NT"),
    "I Pedro": ("la Primera Epístola de San Pedro", False, "NT"),
    "II Pedro": ("la Segunda Epístola de San Pedro", False, "NT"),
    "I Juan": ("la Primera Epístola de San Juan", False, "NT"),
    "II Juan": ("la Segunda Epístola de San Juan", True, "NT"),
    "III Juan": ("la Tercera Epístola de San Juan", True, "NT"),
    "Judas": ("la Epístola de San Judas", True, "NT"),
    "Apocalipsis": ("el Apocalipsis de Nuestro Señor Jesucristo a San Juan", False, "NT"),
    "Tobías": ("el Libro de Tobías", False, "DC"),
    "Judit": ("el Libro de Judit", False, "DC"),
    "Adiciones a Ester": ("el Libro de Ester", False, "DC"),
    "Sabiduría": ("la Sabiduría de Salomón", False, "DC"),
    "Eclesiástico": ("el Eclesiástico, la Sabiduría de Jesús Hijo de Sirá", False, "DC"),
    "Baruc": ("el Libro del Profeta Baruc", False, "DC"),
    "Carta de Jeremías": ("la Carta de Jeremías", True, "DC"),
    "Oración de Azarías": ("la Oración de Azarías", True, "DC"),
    "Susana": ("el libro de Daniel", True, "DC"),
    "Bel y el Dragón": ("Bel y el Dragón", False, "DC"),
    "I Macabeos": ("el Primer Libro de los Macabeos", False, "DC"),
    "II Macabeos": ("el Segundo Libro de los Macabeos", False, "DC"),
    "I Esdras": ("el Primer Libro de Esdras", False, "AP"),
    "II Esdras": ("el Segundo Libro de Esdras", False, "AP"),
    "Oración de Manasés": ("la Oración de Manasés", True, "AP"),
}

books = {
    "Genesis": ("the Book of Genesis", False, "OT"),
    "Exodus": ("the Book of Exodus", False, "OT"),
    "Leviticus": ("the Book of Leviticus", False, "OT"),
    "Numbers": ("the Book of Numbers", False, "OT"),
    "Deuteronomy": ("the Book of Deuteronomy", False, "OT"),
    "Joshua": ("the Book of Joshua", False, "OT"),
    "Judges": ("the Book of Judges", False, "OT"),
    "Ruth": ("the Book of Ruth", False, "OT"),
    "I Samuel": ("the First Book of Samuel", False, "OT"),
    "II Samuel": ("the Second Book of Samuel", False, "OT"),
    "I Kings": ("the First Book of Kings", False, "OT"),
    "II Kings": ("the Second Book of Kings", False, "OT"),
    "I Chronicles": ("the First Book of Chronicles", False, "OT"),
    "II Chronicles": ("the Second Book of Chronicles", False, "OT"),
    "Ezra": ("the Book of Ezra", False, "OT"),
    "Nehemiah": ("the Book of Nehemiah", False, "OT"),
    "Esther": ("the Book of Esther", False, "OT"),
    "Job": ("the Book of Job", False, "OT"),
    "Psalms": ("the Psalms", False, "OT"),
    "Proverbs": ("Proverbs", False, "OT"),
    "Ecclesiastes": ("the Book of Ecclesiastes", False, "OT"),
    "Song of Songs": ("the Song of Songs", False, "OT"),
    "Isaiah": ("the Prophet Isaiah", False, "OT"),
    "Jeremiah": ("the Book of Jeremiah", False, "OT"),
    "Lamentations": ("the Lamentations of Jeremiah", False, "OT"),
    "Ezekiel": ("the Prophet Ezekiel", False, "OT"),
    "Daniel": ("the Prophet Daniel", False, "OT"),
    "Hosea": ("the Prophet Hosea", False, "OT"),
    "Joel": ("the Prophet Joel", False, "OT"),
    "Amos": ("the Prophet Amos", False, "OT"),
    "Obadiah": ("the Prophet Obadiah", True, "OT"),
    "Jonah": ("the Prophet Jonah", False, "OT"),
    "Micah": ("the Prophet Micah", False, "OT"),
    "Nahum": ("the Prophet Nahum", False, "OT"),
    "Habakkuk": ("the Prophet Habakkuk", False, "OT"),
    "Zephaniah": ("the Prophet Zephaniah", False, "OT"),
    "Haggai": ("the Prophet Haggai", False, "OT"),
    "Zechariah": ("the Prophet Zechariah", False, "OT"),
    "Malachi": ("the Prophet Malachi", False, "OT"),
    "Matthew": ("the Gospel of our Lord Jesus Christ according to St. Matthew", False, "NT"),
    "Mark": ("the Gospel of our Lord Jesus Christ according to St. Mark", False, "NT"),
    "Luke": ("the Gospel of our Lord Jesus Christ according to St. Luke", False, "NT"),
    "John": ("the Gospel of our Lord Jesus Christ according to St. John", False, "NT"),
    "Acts": ("the Acts of the Apostles", False, "NT"),
    "Romans": ("St. Paul's Epistle to the Romans", False, "NT"),
    "I Corinthians": ("St. Paul's First Epistle to the Corinthians", False, "NT"),
    "II Corinthians": ("St. Paul's Second Epistle to the Corinthians", False, "NT"),
    "Galatians": ("the Epistle of St. Paul to the Galatians", False, "NT"),
    "Ephesians": ("the Epistle of St. Paul to the Ephesians", False, "NT"),
    "Philippians": ("the Epistle of St. Paul to the Philippians", False, "NT"),
    "Colossians": ("the Epistle of St. Paul to the Colossians", False, "NT"),
    "I Thessalonians": ("St. Paul's First Epistle to the Thessalonians", False, "NT"),
    "II Thessalonians": ("St. Paul's Second Epistle to the Thessalonians", False, "NT"),
    "I Timothy": ("St. Paul's First Epistle to St. Timothy", False, "NT"),
    "II Timothy": ("St. Paul's Second Epistle to St. Timothy", False, "NT"),
    "Titus": ("St. Paul's Epistle to St. Titus", False, "NT"),
    "Philemon": ("St. Paul's Epistle to Philemon", True, "NT"),
    "Hebrews": ("the Epistle to the Hebrews", False, "NT"),
    "James": ("the Epistle of St. James", False, "NT"),
    "I Peter": ("the First Epistle of St. Peter", False, "NT"),
    "II Peter": ("the Second Epistle of St. Peter", False, "NT"),
    "I John": ("the First Epistle of St. John", False, "NT"),
    "II John": ("the Second Epistle of St. John", True, "NT"),
    "III John": ("the Third Epistle of St. John", True, "NT"),
    "Jude": ("the Epistle of St. Jude", True, "NT"),
    "Revelation": ("the Revelation of Our Lord Jesus Christ to St. John", False, "NT"),
    "Tobit": ("the Book of Tobit", False, "DC"),
    "Judith": ("the Book of Judith", False, "DC"),
    "Additions to Esther": ("the Book of Esther", False, "DC"),
    "Wisdom": ("the Wisdom of Solomon", False, "DC"),
    "Sirach": ("Ecclesiasticus, the Wisdom of Jesus Son of Sirach", False, "DC"),
    "Baruch": ("the Book of Baruch the Prophet", False, "DC"),
    "Letter of Jeremiah": ("the Letter of Jeremiah", True, "DC"),
    "Prayer of Azariah": ("Prayer of Azariah", True, "DC"),
    "Susanna": ("the book of Daniel", True, "DC"),
    "Bel and the Dragon": ("Bel and the Dragon", False, "DC"),
    "I Maccabees": ("the First Book of the Maccabees", False, "DC"),
    "II Maccabees": ("the Second Book of the Maccabees", False, "DC"),
    "I Esdras": ("the First Book of Esdras", False, "AP"),
    "II Esdras": ("the Second Book of Esdras", False, "AP"),
    "Prayer of Manasseh": ("Prayer of Manasseh", True, "AP"),
}


def passage_to_citation_english(passage, mass=False):
    if not passage:
        return None

    passage = scriptures.extract(passage)
    passage = passage[0]

    if not passage:
        return None

    if passage[0] == "Susanna":
        return "The Book of Daniel, beginning with thirteenth chapter, the first verse, the Story of Susanna"

    book_name = passage[0]
    if book_name == "Song of Solomon":
        book_name = "Song of Songs"

    if book_name == "Revelation of Jesus Christ":
        book_name = "Revelation"

    book = books[book_name]

    if book_name in ["Matthew", "Mark", "Luke", "John"] and mass:
        return book[0].replace("the ", "The Holy ")

    if book[1]:  # 1 chapter book
        return "A reading from {}, beginning with the {} verse".format(book[0], num2words(passage[2], ordinal=True))

    return "A reading from {}, beginning with the {} chapter, the {} verse".format(
        book[0], num2words(passage[1], ordinal=True), num2words(passage[2], ordinal=True)
    )


def passage_to_citation_spanish(passage, mass=False):
    if not passage:
        return None

    passage = scriptures.extract(passage)
    passage = passage[0]

    if not passage:
        return None

    if passage[0] == "Susanna":
        return "El Libro de Daniel, comenzando con el capítulo trece, el versículo primero, la Historia de Susana"

    book_name = passage[0]
    if book_name == "Song of Solomon":
        book_name = "Song of Songs"

    if book_name == "Revelation of Jesus Christ":
        book_name = "Revelation"

    # Convert English book name to Spanish
    spanish_book_name = english_to_spanish.get(book_name, book_name)
    book = spanish_books[spanish_book_name]

    if book_name in ["Matthew", "Mark", "Luke", "John"] and mass:
        return book[0].replace("el Santo Evangelio", "El Santo Evangelio")

    if book[1]:  # 1 chapter book
        return "Una lectura de {}, comenzando con el versículo {}".format(
            book[0], num2words(passage[2], ordinal=True, lang="es")
        )

    return "Una lectura de {}, comenzando con el capítulo {}, el versículo {}".format(
        book[0], num2words(passage[1], ordinal=True, lang="es"), num2words(passage[2], ordinal=True, lang="es")
    )


def passage_to_citation(passage, mass=False, language_style="contemporary"):
    if language_style == "spanish":
        return passage_to_citation_spanish(passage, mass)
    else:
        return passage_to_citation_english(passage, mass)


def testament_to_closing(testament):
    return "The Word of the Lord." if testament != "DC" else "Here ends the Reading."


def testament_to_closing_response(testament):
    return "Thanks be to God." if testament != "DC" else ""


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


# https://www.geeksforgeeks.org/convert-string-to-title-case-in-python/
def title_case(input_string):
    input_string = input_string.lower()
    # list of articles
    articles = ["a", "an", "the"]

    # list of coordinating conjunctins
    conjunctions = ["and", "but", "for", "nor", "or", "so", "yet"]

    # list of some short articles
    prepositions = [
        "in",
        "to",
        "for",
        "with",
        "on",
        "at",
        "from",
        "by",
        "about",
        "as",
        "into",
        "like",
        "through",
        "after",
        "over",
        "between",
        "out",
        "against",
        "during",
        "without",
        "before",
        "under",
        "around",
        "among",
        "of",
    ]

    additions = []

    all_caps = ["i", "ii", "iii", "(i)", "(ii)", "(iii)"]

    # merging the 3 lists
    lower_case = articles + conjunctions + prepositions + additions

    # variable declaration for the output text
    output_string = ""

    # separating each word in the string
    input_list = input_string.split(" ")

    # checking each word
    for i, word in enumerate(input_list):
        if word in all_caps:
            output_string += word.upper() + " "

        # if the word exists in the list
        # then no need to capitalize it
        elif i != 0 and word in lower_case:
            output_string += word + " "

        # if the word does not exists in
        # the list, then capitalize it
        else:
            temp = word.title()
            output_string += temp + " "

    return output_string


import uuid


def generate_uuid_from_string(input_string: str) -> str:
    namespace = uuid.NAMESPACE_DNS
    generated_uuid = uuid.uuid5(namespace, input_string)
    return str(generated_uuid)


def passage_reference_to_spanish(passage: str) -> str:
    if not passage:
        return passage

    match = re.match(r"^(\s*)(.*?)(\s*)$", passage, re.DOTALL)
    if not match:
        return passage

    leading_ws, core, trailing_ws = match.groups()

    for book_name in sorted(english_to_spanish, key=len, reverse=True):
        if core.startswith(book_name):
            next_index = len(book_name)
            if next_index == len(core) or not core[next_index].isalnum():
                translated = english_to_spanish[book_name]
                return f"{leading_ws}{translated}{core[next_index:]}{trailing_ws}"

    return passage
