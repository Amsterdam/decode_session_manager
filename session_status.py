from enum import Enum

class SessionStatus(Enum):
    INITIALIZED = 'INITIALIZED'
    GOT_PUB_KEY = 'GOT_PUB_KEY'
    GOT_ENCR_DATA = 'GOT_ENCR_DATA'
    FINALIZED = 'FINALIZED'
