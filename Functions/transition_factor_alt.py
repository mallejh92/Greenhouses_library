from Functions.transition_factor import transition_factor

class transition_factor_alt(transition_factor):
    """
    Class for calculating weighting factor with alternative transition range definition
    """
    
    def calculate(self, switch: float = 0.5, trans: float = None, 
                 position: float = 0.0, order: int = 2) -> float:
        """
        Calculate weighting factor with alternative transition range definition
        
        Parameters:
            switch (float): Centre of transition interval
            trans (float): Transition duration (default: 0.05 * switch)
            position (float): Current position
            order (int): Smooth up to which derivative?
            
        Returns:
            float: Weighting factor
        """
        # Calculate transition duration if not provided
        if trans is None:
            trans = 0.05 * switch
            
        # Calculate start and stop points
        start = switch - 0.5 * trans
        stop = switch + 0.5 * trans
        
        # Call parent class calculate method
        return super().calculate(start=start, stop=stop, 
                               position=position, order=order)
