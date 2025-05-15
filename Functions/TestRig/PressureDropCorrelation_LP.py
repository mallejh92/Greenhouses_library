def PressureDropCorrelation_LP(M_flow: float) -> float:
    """
    Calculate pressure drop in the low pressure line
    
    This function calculates the pressure drop in the low pressure line of the ORCNext setup
    based on the mass flow rate.
    
    Parameters:
        M_flow (float): Mass flow rate [kg/s]
        
    Returns:
        float: Pressure drop [Pa]
    """
    # Constants
    k1 = 38453.9
    k2 = 23282.7
    
    # Calculate pressure drop
    DELTAp = k1 * M_flow + k2 * M_flow**2
    
    return DELTAp
