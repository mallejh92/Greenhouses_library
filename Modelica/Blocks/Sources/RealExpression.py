class RealExpression:
    """
    Modelica.Blocks.Sources.RealExpression의 Python 구현
    
    Set output signal to a time varying Real expression
    
    The (time varying) Real output signal of this block can be defined in its 
    parameter menu via variable y. The purpose is to support the easy definition 
    of Real expressions in a block diagram.
    
    Parameters:
    -----------
    y : float
        Value of Real output (both parameter and connector)
    
    Attributes:
    -----------
    y : float
        Value of Real output (both parameter and connector)
    """
    
    def __init__(self, y=0.0):
        """
        Initialize RealExpression block
        
        Parameters:
        -----------
        y : float
            Initial value of Real output (both parameter and connector)
        """
        self.y = y
        self._connected_components = []
    
    def set_expression(self, y):
        """
        Set the expression output value
        
        Parameters:
        -----------
        y : float
            New output value
        """
        self.y = y
        # 연결된 컴포넌트들에게 값 전파
        self._propagate_value()
    
    def get_output(self):
        """
        Get the current output value
        
        Returns:
        --------
        float
            Current output value
        """
        return self.y
    
    def connect(self, target_component, target_attribute=None):
        """
        Connect this RealExpression to another component
        
        Parameters:
        -----------
        target_component : object
            Target component to connect to
        target_attribute : str, optional
            Target attribute name (default: 'y')
        """
        if target_attribute is None:
            target_attribute = 'y'
        
        connection = {
            'component': target_component,
            'attribute': target_attribute
        }
        
        if connection not in self._connected_components:
            self._connected_components.append(connection)
            # 초기값 전파
            setattr(target_component, target_attribute, self.y)
    
    def disconnect(self, target_component, target_attribute=None):
        """
        Disconnect this RealExpression from another component
        
        Parameters:
        -----------
        target_component : object
            Target component to disconnect from
        target_attribute : str, optional
            Target attribute name (default: 'y')
        """
        if target_attribute is None:
            target_attribute = 'y'
        
        connection = {
            'component': target_component,
            'attribute': target_attribute
        }
        
        if connection in self._connected_components:
            self._connected_components.remove(connection)
    
    def _propagate_value(self):
        """연결된 모든 컴포넌트에게 현재 값을 전파"""
        for connection in self._connected_components:
            component = connection['component']
            attribute = connection['attribute']
            try:
                setattr(component, attribute, self.y)
            except AttributeError:
                # 속성이 없는 경우 무시
                pass
    
    def update(self, time=None, **kwargs):
        """
        Update the expression value (for time-varying expressions)
        
        Parameters:
        -----------
        time : float, optional
            Current simulation time
        **kwargs : dict
            Additional parameters for expression evaluation
        """
        # 기본적으로는 단순히 현재 값을 유지
        # 시간에 따른 표현식이 필요한 경우 이 메서드를 오버라이드
        pass
    
    def step(self, dt, time=None):
        """
        Step the expression (for time-varying expressions)
        
        Parameters:
        -----------
        dt : float
            Time step
        time : float, optional
            Current simulation time
        """
        # 시간에 따른 표현식 업데이트
        self.update(time=time)
        # 연결된 컴포넌트들에게 값 전파
        self._propagate_value()
    
    def __str__(self):
        """String representation of the RealExpression"""
        return f"RealExpression(y={self.y})"
    
    def __repr__(self):
        """Detailed string representation of the RealExpression"""
        return f"RealExpression(y={self.y}, connected_to={len(self._connected_components)}_components)" 