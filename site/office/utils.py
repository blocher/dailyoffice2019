import scriptures
from num2words import num2words

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
    "I John": ("the First Epistle of St. John", True, "NT"),
    "II John": ("the Second Epistle of St. John", True, "NT"),
    "III John": ("the Third Epistle of St. John", False, "NT"),
    "Jude": ("the Epistle of St. Jude", True, "NT"),
    "Revelation": ("Revelation of Our Lord Jesus Christ to St. John", False, "NT"),
    "Tobit": ("the Book of Tobit", False, "DC"),
    "Judith": ("the Book of Judith", False, "DC"),
    "Additions to Esther": ("the Book of Esther", False, "DC"),
    "The Wisdom of Solomon": ("the Wisdom of Solomon", False, "DC"),
    "Sirach": ("Ecclesiasticus, the Wisdom of Jesus Son of Sirach ", False, "DC"),
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


def passage_to_citation(passage):

    if not passage:
        return None

    passage = scriptures.extract(passage)[0]

    if not passage:
        return None

    if passage[0] == "Susanna":
        return "The Book of Daniel, beginning with thirteenth chapter, the first verse, the Story of Susanna"

    book_name = passage[0]
    if book_name == "Song of Solomon":
        book_name = "Song of Songs"

    book = books[book_name]

    if book[1]:  # 1 chapter book
        return "A reading from {}, beginning with the {} verse".format(book[0], num2words(passage[2], ordinal=True))

    return "A reading from {}, beginning with the {} chapter, the {} verse".format(
        book[0], num2words(passage[1], ordinal=True), num2words(passage[2], ordinal=True)
    )
