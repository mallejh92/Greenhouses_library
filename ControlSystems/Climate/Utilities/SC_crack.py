class SC_crack:
    """
    Timer measuring the time from the time instant where the Boolean input became true
    """
    
    def __init__(self, SC_value: float):
        """
        Initialize SC crack calculator
        
        Parameters:
            SC_value (float): Screen value from 0 to 1
        """
        self.SC_value = SC_value
        self.entryTime = 0.0  # Time instant when u became true
        
    def update(self, u: bool, time: float) -> float:
        """
        Update SC crack value
        
        Parameters:
            u (bool): Boolean input signal
            time (float): Current simulation time [s]
            
        Returns:
            float: Output signal value
        """
        # Update entry time when input becomes true
        if u:
            self.entryTime = time
            
        # Return SC value if input is true, otherwise return 0
        return self.SC_value if u else 0.0
