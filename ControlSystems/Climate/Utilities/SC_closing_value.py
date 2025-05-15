from .SC_opening_closing import SC_opening_closing

class SC_closing_value:
    """
    Timer measuring the time from the time instant where the Boolean input became true
    """
    
    def __init__(self, warmDay: bool = True, opening: bool = True):
        """
        Initialize SC closing value calculator
        
        Parameters:
            warmDay (bool): True if warm day, False if cold day
            opening (bool): True if opening, False if closing
        """
        self.warmDay = warmDay
        self.opening = opening
        self.entryTime = 0.0  # Time instant when u became true
        self.SC_value = SC_opening_closing(warmDay=warmDay, opening=opening)
        
    def update(self, u: bool, time: float) -> float:
        """
        Update SC closing value
        
        Parameters:
            u (bool): Boolean input signal
            time (float): Current simulation time [s]
            
        Returns:
            float: Output signal value
        """
        # Update entry time when input becomes true
        if u:
            self.entryTime = time
            
        # Update SC value calculator
        self.SC_value.update(self.entryTime, time)
        
        # Return SC value if input is true, otherwise return 0
        return self.SC_value.y if u else 0.0
