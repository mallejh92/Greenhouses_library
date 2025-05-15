from Functions.SaturatedVapourPressure import SaturatedVapourPressure

class WaterVapourPressure:
    """
    Class for calculating water vapour pressure of a gas computed by the relative humidity 
    and the saturation water vapour pressure at the gas temperature
    """
    
    def calculate(self, TSat: float, RH: float) -> float:
        """
        Calculate water vapour pressure using relative humidity and saturation temperature
        
        Parameters:
            TSat (float): Saturation temperature [°C]
            RH (float): Relative humidity [%] (0...100)
            
        Returns:
            float: Water vapour pressure [Pa]
        """
        sat_pressure = SaturatedVapourPressure().calculate(TSat)
        VP = RH / 100 * sat_pressure
        return VP
