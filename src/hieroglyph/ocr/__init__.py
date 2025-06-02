import string


ENGLISH_PRINTABLE = set(string.ascii_letters)
PUNCTUATION_WHITESPACE = set(string.punctuation + '一_…”' + string.whitespace)
ENGLISH_PUNCTUATION_WHITESPACE = ENGLISH_PRINTABLE.union(PUNCTUATION_WHITESPACE)

# Make Adjustable
DIAGRAM_CONFIDENCE_THRESHOLD = 35.0
TABLE_CONFIDENCE_THRESHOLD = 40.0
TEXT_CONFIDENCE_THRESHOLD = 50.0

CHARACTER_BLACKLIST = '『「_”【…，、〇|♪'
# NOTE: Keep an eye out for CJK symbols and punctuation
