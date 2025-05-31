class RealExpression:
    """
    The (time varying) Real output signal of this block can be defined in its parameter menu via variable y.
    The purpose is to support the easy definition of Real expressions in a block diagram.
    For example, in the y-menu the definition "if time < 1 then 0 else 1" can be given in order to define
    that the output signal is one, if time ≥ 1 and otherwise it is zero.
    Note, that "time" is a built-in variable that is always accessible and represents the "model time"
    and that variable y is both a variable and a connector.
    """
    def __init__(self, y=None, time=0.0):
        """
        Initialize RealExpression
        
        Parameters:
        -----------
        y : callable or float, optional
            Expression or value for the output signal. If callable, it should take 'time' as an argument.
            Example: lambda time: 0 if time < 1 else 1
        time : float, optional
            Current simulation time [s]
        """
        self._y = y if y is not None else 0.0
        self._time = time
        self._connected_blocks = []

    @property
    def y(self):
        """Get current output value"""
        if callable(self._y):
            return self._y(self._time)
        return self._y

    @y.setter
    def y(self, value):
        """Set output expression or value"""
        self._y = value

    @property
    def time(self):
        """Get current simulation time"""
        return self._time

    @time.setter
    def time(self, value):
        """Set current simulation time"""
        self._time = float(value)

    def connect(self, block):
        """
        Connect this expression to another block
        
        Parameters:
        -----------
        block : object
            Block to connect to. The block should have a 'y' attribute or property.
        """
        if block not in self._connected_blocks:
            self._connected_blocks.append(block)

    def calculate(self):
        """Calculate and propagate the output value to connected blocks"""
        current_value = self.y
        for block in self._connected_blocks:
            if hasattr(block, 'y'):
                block.y = current_value
            elif hasattr(block, 'T'):
                block.T = current_value
            # Add more connection types as needed

    def step(self, dt):
        """
        Advance simulation time and update output
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        self._time += dt
        self.calculate()
        return self.y

    def set_expression(self, expr):
        """
        Set a time-dependent expression
        
        Parameters:
        -----------
        expr : str or callable
            Expression as a string or callable function.
            If string, it will be converted to a lambda function.
            Example: "if time < 1 then 0 else 1"
        """
        if isinstance(expr, str):
            # Convert string expression to lambda function
            # Note: This is a simple implementation. For complex expressions,
            # you might want to use a proper expression parser
            try:
                # Replace Modelica-style 'then' with Python 'if'
                expr = expr.replace('then', 'if').replace('else', 'else:')
                # Create lambda function
                self._y = eval(f"lambda time: {expr}")
            except Exception as e:
                print(f"Error parsing expression: {e}")
                raise
        else:
            self._y = expr 