import arabic_reshaper
from bidi.algorithm import get_display

def ar(t):
    if any('\u0600' <= c <= '\u06FF' for c in t):
        return get_display(arabic_reshaper.reshape(t))
    return t
