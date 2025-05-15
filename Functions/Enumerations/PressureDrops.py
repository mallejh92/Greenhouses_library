from enum import Enum

class PressureDrops(Enum):
    """
    Types of pressure drop models
    
    Attributes:
        UD: User defined pressure drop model
        ORCnextHP: High pressure line of the ORCNext setup
        ORCnextLP: Low pressure line of the ORCNext setup
    """
    UD = "User defined"
    ORCnextHP = "High pressure line of the ORCNext setup"
    ORCnextLP = "Low pressure line of the ORCNext setup"
