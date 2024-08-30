__version__ = "0.1dev"


_OPENAI_KEY = None
_OPENAI_MODEL = None


def set_openai_key(key: str):
    global _OPENAI_KEY
    _OPENAI_KEY = key


def get_openai_key():
    return _OPENAI_KEY


def set_openai_model(model: str):
    global _OPENAI_MODEL
    _OPENAI_MODEL = model


def get_openai_model():
    return _OPENAI_MODEL
