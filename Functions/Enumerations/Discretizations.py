from enum import Enum

class Discretizations(Enum):
    """
    Spatial discretization schemes for fluid flow and heat transfer modeling
    
    Attributes:
        centr_diff: Central Difference Scheme - Basic
        centr_diff_AllowFlowReversal: Central Difference Scheme - Allows Reverse Flow
        upwind: Upwind Scheme - Basic
        upwind_AllowFlowReversal: Upwind Scheme - Allows Flow Reversal and zero flow
        upwind_smooth: Upwind Scheme with Smoothing
    """
    centr_diff = "Central Difference Scheme - Basic"
    centr_diff_AllowFlowReversal = "Central Difference Scheme - Allows Reverse Flow"
    upwind = "Upwind Scheme - Basic"
    upwind_AllowFlowReversal = "Upwind Scheme - Allows Flow Reversal and zero flow"
    upwind_smooth = "Upwind Scheme with Smoothing"
