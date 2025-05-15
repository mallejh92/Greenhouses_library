from .Ramp import Ramp

class SC_opening_closing:
    """
    Screen closing/opening control for warm/cold days
    """
    
    def __init__(self, warmDay: bool = True, opening: bool = True):
        """
        Initialize screen control
        
        Parameters:
            warmDay (bool): True if warm day, False if cold day
            opening (bool): True if opening, False if closing
        """
        self.warmDay = warmDay
        self.opening = opening
        self.entryTime = 0.0
        
        # Initialize ramps for warm day opening
        self.o1 = Ramp(duration=60, height=-0.01)
        self.o2 = Ramp(duration=60, height=-0.02)
        self.o3 = Ramp(duration=60, height=-0.03)
        self.o4 = Ramp(duration=60, height=-0.04)
        self.o5 = Ramp(duration=60, height=-0.04)
        self.o6 = Ramp(duration=60, height=-0.05)
        self.o7 = Ramp(duration=60, height=-0.05)
        self.o8 = Ramp(duration=60, height=-0.06)
        self.o9 = Ramp(duration=60, height=-0.7)
        
        # Initialize ramps for cold day opening
        self.c1 = Ramp(duration=60, height=-0.01)
        self.c2 = Ramp(duration=60, height=-0.01)
        self.c3 = Ramp(duration=60, height=-0.01)
        self.c4 = Ramp(duration=60, height=-0.01)
        self.c5 = Ramp(duration=60, height=-0.02)
        self.c6 = Ramp(duration=60, height=-0.02)
        self.c7 = Ramp(duration=60, height=-0.02)
        self.c8 = Ramp(duration=60, height=-0.03)
        self.c9 = Ramp(duration=60, height=-0.03)
        self.c10 = Ramp(duration=60, height=-0.04)
        self.c11 = Ramp(duration=60, height=-0.04)
        self.c12 = Ramp(duration=60, height=-0.04)
        self.c13 = Ramp(duration=60, height=-0.04)
        self.c14 = Ramp(duration=60, height=-0.68)
        
        # Initialize ramps for cold day closing
        self.c15 = Ramp(duration=60, height=-0.68)
        self.c16 = Ramp(duration=60, height=-0.04)
        self.c17 = Ramp(duration=60, height=-0.04)
        self.c18 = Ramp(duration=60, height=-0.04)
        self.c19 = Ramp(duration=60, height=-0.04)
        self.c20 = Ramp(duration=60, height=-0.03)
        self.c21 = Ramp(duration=60, height=-0.03)
        self.c22 = Ramp(duration=60, height=-0.02)
        self.c23 = Ramp(duration=60, height=-0.02)
        self.c24 = Ramp(duration=60, height=-0.02)
        self.c25 = Ramp(duration=60, height=-0.01)
        self.c26 = Ramp(duration=60, height=-0.01)
        self.c27 = Ramp(duration=60, height=-0.01)
        self.c28 = Ramp(duration=60, height=-0.01)
        
        # Output value
        self.y = 0.0
        
    def update(self, entryTime: float, time: float) -> float:
        """
        Update screen control value
        
        Parameters:
            entryTime (float): Time when control started [s]
            time (float): Current simulation time [s]
            
        Returns:
            float: Control signal value
        """
        self.entryTime = entryTime
        
        # Update ramp start times
        self._update_ramp_times()
        
        # Calculate output based on conditions
        if self.warmDay:
            if self.opening:
                self.y = (1.0 + self.o1.update(time) + self.o2.update(time) + 
                         self.o3.update(time) + self.o4.update(time) + 
                         self.o5.update(time) + self.o6.update(time) + 
                         self.o7.update(time) + self.o8.update(time) + 
                         self.o9.update(time))
            else:
                self.y = (0.0 - self.o9.update(time) - self.o8.update(time) - 
                         self.o7.update(time) - self.o6.update(time) - 
                         self.o5.update(time) - self.o4.update(time) - 
                         self.o3.update(time) - self.o2.update(time) - 
                         self.o1.update(time))
        else:
            if self.opening:
                self.y = (1.0 + self.c1.update(time) + self.c2.update(time) + 
                         self.c3.update(time) + self.c4.update(time) + 
                         self.c5.update(time) + self.c6.update(time) + 
                         self.c7.update(time) + self.c8.update(time) + 
                         self.c9.update(time) + self.c10.update(time) + 
                         self.c11.update(time) + self.c12.update(time) + 
                         self.c13.update(time) + self.c14.update(time))
            else:
                self.y = (0.0 - self.c15.update(time) - self.c16.update(time) - 
                         self.c17.update(time) - self.c18.update(time) - 
                         self.c19.update(time) - self.c20.update(time) - 
                         self.c21.update(time) - self.c22.update(time) - 
                         self.c23.update(time) - self.c24.update(time) - 
                         self.c25.update(time) - self.c26.update(time) - 
                         self.c27.update(time) - self.c28.update(time))
        
        return self.y
        
    def _update_ramp_times(self):
        """Update start times for all ramps"""
        # Warm day opening ramps
        self.o1.startTime = self.entryTime + 0
        self.o2.startTime = self.entryTime + 4*60
        self.o3.startTime = self.entryTime + 8*60
        self.o4.startTime = self.entryTime + 12*60
        self.o5.startTime = self.entryTime + 16*60
        self.o6.startTime = self.entryTime + 20*60
        self.o7.startTime = self.entryTime + 24*60
        self.o8.startTime = self.entryTime + 28*60
        self.o9.startTime = self.entryTime + 32*60
        
        # Cold day opening ramps
        self.c1.startTime = self.entryTime + 0
        self.c2.startTime = self.entryTime + 4*60
        self.c3.startTime = self.entryTime + 8*60
        self.c4.startTime = self.entryTime + 12*60
        self.c5.startTime = self.entryTime + 16*60
        self.c6.startTime = self.entryTime + 20*60
        self.c7.startTime = self.entryTime + 24*60
        self.c8.startTime = self.entryTime + 28*60
        self.c9.startTime = self.entryTime + 32*60
        self.c10.startTime = self.entryTime + 36*60
        self.c11.startTime = self.entryTime + 40*60
        self.c12.startTime = self.entryTime + 44*60
        self.c13.startTime = self.entryTime + 48*60
        self.c14.startTime = self.entryTime + 52*60
        
        # Cold day closing ramps
        self.c15.startTime = self.entryTime + 0
        self.c16.startTime = self.entryTime + 4*60
        self.c17.startTime = self.entryTime + 8*60
        self.c18.startTime = self.entryTime + 12*60
        self.c19.startTime = self.entryTime + 16*60
        self.c20.startTime = self.entryTime + 20*60
        self.c21.startTime = self.entryTime + 24*60
        self.c22.startTime = self.entryTime + 28*60
        self.c23.startTime = self.entryTime + 32*60
        self.c24.startTime = self.entryTime + 36*60
        self.c25.startTime = self.entryTime + 40*60
        self.c26.startTime = self.entryTime + 44*60
        self.c27.startTime = self.entryTime + 48*60
        self.c28.startTime = self.entryTime + 52*60
