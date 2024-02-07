from enum import Enum


class Language(Enum):
    ENGLISH = "eng"
    SWEDISH = "swe"
    DANISH = "dan"
    LATIN = "lat"
    ICELANDIC = "ice"
    FAROESE = "fao"
    GREENLANDIC = "kal"
    FINNISH = "fin"
    NORWEGIAN = "nor"
    SPANISH = "spa"
    HUNGARIAN = "hun"
    GERMAN = "ger"


class PublicationStatus(Enum):
    PUBLISHED = "Published"
    EPUB_AHEAD_OF_PRINT = "Epub ahead of print"
    IN_PRESS = "In press"
    ACCEPTED = "Accepted"
    SUBMITTED = "Submitted"


class PublicationType(Enum):
    ARTICLE_JOURNAL = "article-journal"
    ARTICLE_NEWSPAPER = "article-newspaper"
    BOOK = "book"
    CHAPTER = "chapter"
    CONFERENCE_PAPER = "paper-conference"
    DATASET = "dataset"
    DISSERTATION = "dissertation"
    MANUSCRIPT = "manuscript"
    REPORT = "report"
    REVIEW = "review"
    REVIEW_BOOK = "review-book"
    SONG = "song"
    SPEECH = "speech"
    THESIS = "thesis"
