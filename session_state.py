# session_state.py

class SessionState(object):
    _state = {}

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

    @classmethod
    def get(cls, **kwargs):
        if not cls._state:
            cls._state = cls(**kwargs)
        return cls._state