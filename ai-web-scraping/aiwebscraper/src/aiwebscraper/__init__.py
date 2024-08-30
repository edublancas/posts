__version__ = "0.1dev"


_OPENAI_KEY = None


def set_openai_key(key: str):
    global _OPENAI_KEY
    _OPENAI_KEY = key


def get_openai_key():
    return _OPENAI_KEY
