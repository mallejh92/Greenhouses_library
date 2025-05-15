def PressureDropCorrelation_HP(M_flow: float) -> float:
    """
    Calculate pressure drop in the high pressure line
    
    This function calculates the pressure drop in the high pressure line of the ORCNext setup
    based on the mass flow rate.
    
    Parameters:
        M_flow (float): Mass flow rate [kg/s]
        
    Returns:
        float: Pressure drop [Pa]
    """
    # Constants
    k1 = 11857.8
    k2 = 77609.9
    
    # Calculate pressure drop
    DELTAp = k1 * M_flow + k2 * M_flow**2
    
    return DELTAp
