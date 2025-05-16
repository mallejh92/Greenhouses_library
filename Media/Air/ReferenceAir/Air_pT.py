class Air_pT:
    """
    Reference air properties model.
    This class provides methods to calculate air properties based on pressure and temperature.
    The calculations are based on the ideal gas law and standard air properties.
    
    Constants:
        R_air (float): Specific gas constant for air in J/(kg·K)
        M_air (float): Molar mass of air in kg/mol
    """
    
    # Constants
    R_air = 287.0  # Specific gas constant for air in J/(kg·K)
    M_air = 0.02897  # Molar mass of air in kg/mol
    
    @staticmethod
    def density_pT(p: float, T: float) -> float:
        """
        Calculate air density based on pressure and temperature using the ideal gas law.
        
        Args:
            p (float): Pressure in Pa
            T (float): Temperature in K
            
        Returns:
            float: Air density in kg/m3
        """
        return p / (Air_pT.R_air * T)
    
    @staticmethod
    def specific_heat_capacity_pT(p: float, T: float) -> float:
        """
        Calculate specific heat capacity of air at constant pressure.
        This is a simplified model that returns a constant value for standard conditions.
        
        Args:
            p (float): Pressure in Pa
            T (float): Temperature in K
            
        Returns:
            float: Specific heat capacity in J/(kg·K)
        """
        return 1005.0  # Constant value for standard conditions
    
    @staticmethod
    def thermal_conductivity_pT(p: float, T: float) -> float:
        """
        Calculate thermal conductivity of air.
        This is a simplified model that returns a constant value for standard conditions.
        
        Args:
            p (float): Pressure in Pa
            T (float): Temperature in K
            
        Returns:
            float: Thermal conductivity in W/(m·K)
        """
        return 0.0262  # Constant value for standard conditions
    
    @staticmethod
    def dynamic_viscosity_pT(p: float, T: float) -> float:
        """
        Calculate dynamic viscosity of air.
        This is a simplified model that returns a constant value for standard conditions.
        
        Args:
            p (float): Pressure in Pa
            T (float): Temperature in K
            
        Returns:
            float: Dynamic viscosity in Pa·s
        """
        return 1.84e-5  # Constant value for standard conditions 