from .langbase import LANGBASE
from .pg_languages import PG_LANGUAGES

def format_indexable_language_fields(lang_code=None, langbase=LANGBASE):
    if lang_code:
        if "-" in lang_code:
            lang_code = lang_code.split("-")[0]
        if len(lang_code) == 2:
            language_data = [x for x in langbase if x[1] == lang_code]
            if language_data:
                if language_data[0][-1].lower() in PG_LANGUAGES:
                    pg_lang = language_data[0][-1].lower()
                else:
                    pg_lang = None
                return {
                    "language_iso639_2": language_data[0][0],
                    "language_iso639_1": language_data[0][1],
                    "language_display": language_data[0][-1].lower(),
                    "language_pg": pg_lang,
                }
        elif len(lang_code) == 3:
            language_data = [x for x in langbase if x[0] == lang_code]
            if language_data:
                if language_data[0][-1].lower() in PG_LANGUAGES:
                    pg_lang = language_data[0][-1].lower()
                else:
                    pg_lang = None
                return {
                    "language_iso639_2": language_data[0][0],
                    "language_iso639_1": language_data[0][1],
                    "language_display": language_data[0][-1].lower(),
                    "language_pg": pg_lang,
                }
    return {
        "language_iso639_2": None,
        "language_iso639_1": None,
        "language_display": None,
        "language_pg": None,
    }


