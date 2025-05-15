class Ramp:
    """
    Generate ramp signal with configurable height, duration, and offset
    """
    
    def __init__(self, height: float = 1.0, duration: float = 2.0, offset: float = 0.0):
        """
        Initialize Ramp generator
        
        Parameters:
            height (float): Height of ramps
            duration (float): Duration of ramp in seconds (0.0 gives a Step)
            offset (float): Offset of output signal
        """
        self.height = height
        self.duration = duration
        self.offset = offset
        self.startTime = 0.0  # Output = offset for time < startTime
        
    def update(self, time: float) -> float:
        """
        Update ramp signal
        
        Parameters:
            time (float): Current simulation time [s]
            
        Returns:
            float: Ramp signal value
        """
        if time < self.startTime:
            return self.offset
        elif time < (self.startTime + self.duration):
            return self.offset + (time - self.startTime) * self.height / self.duration
        else:
            return self.offset + self.height
