from enum import Enum
from typing import Dict, Any, Optional

class ScreenType(Enum):
    WELCOME = "welcome"
    LOGIN = "login"
    CARD = "card"
    CATALOG = "catalog"
    CHARGE= "charge"