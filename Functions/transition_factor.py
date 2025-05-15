import numpy as np
from math import pi, e

class transition_factor:
    """
    Class for calculating weighting factor for smooth transition (from 0 to 1)
    """
    
    def __init__(self):
        # First parameters
        self.a_map = [-1/2, -2/pi, -3/4, -8/pi]
        # Second parameters
        self.b_map = [1/2, 1/2, 1/2, 1/2]
        
        # Parameters for generalised logistic function
        self.A = 0  # Lower asymptote
        self.K = 1  # Upper asymptote
        self.B = 8  # Growth rate
        self.nu = 1  # Symmetry changes
        self.Q = self.nu  # Zero correction
        self.M = self.nu  # Maximum growth for Q = nu
    
    def calculate(self, start: float = 0.25, stop: float = 0.75, 
                 position: float = 0.0, order: int = 2) -> float:
        """
        Calculate weighting factor for smooth transition
        
        Parameters:
            start (float): Start of transition interval
            stop (float): End of transition interval
            position (float): Current position
            order (int): Smooth up to which derivative?
            
        Returns:
            float: Weighting factor
        """
        # Input validation
        assert order >= 0, "This function only supports positive values for the order of smooth derivatives."
        assert start < stop, "There is only support for positive differences, please provide start < stop."
        
        # Return 1 or 0 if outside transition interval
        if position < start:
            return 1
        elif position > stop:
            return 0
        
        # Calculate transition factor based on order
        if order <= 2:
            # 0th to 2nd order
            a = self.a_map[order]
            b = self.b_map[order]
            DELTAx = stop - start
            x_t = start + 0.5 * DELTAx
            phi = (position - x_t) / DELTAx * pi
            
            if order == 0:
                return a * np.sin(phi) + b
            elif order == 1:
                return a * (0.5 * np.cos(phi) * np.sin(phi) + 0.5 * phi) + b
            elif order == 2:
                return a * (1/3 * np.cos(phi)**2 * np.sin(phi) + 2/3 * np.sin(phi)) + b
        else:
            # Higher order using generalised logistic function
            END = 4.0
            START = -2.0
            factor = (END - START) / (stop - start)
            X = START + (position - start) * factor
            
            return 1 - (self.A + (self.K - self.A) / (1 + self.Q * e**(-self.B * (X - self.M)))**(1/self.nu))
