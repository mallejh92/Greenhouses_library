import numpy as np

class Illumination:
    """
    Python version of Greenhouses.Components.Greenhouse.Illumination.
    Simulates artificial lighting radiation (HPS lamps) absorbed by air, canopy, and floor.
    """

    def __init__(self,
                 power_input=False,
                 P_el=0.0,
                 A=1.0,
                 p_el=55.0,
                 K1_PAR=0.7,
                 K2_PAR=0.7,
                 K_NIR=0.27,
                 rho_CanPAR=0.07,
                 rho_CanNIR=0.35,
                 rho_FlrPAR=0.07,
                 rho_FlrNIR=0.07,
                 eta_GlobPAR=1.8):
        self.power_input = power_input
        self.P_el = P_el
        self.A = A
        self.p_el = p_el
        self.K1_PAR = K1_PAR
        self.K2_PAR = K2_PAR
        self.K_NIR = K_NIR
        self.rho_CanPAR = rho_CanPAR
        self.rho_CanNIR = rho_CanNIR
        self.rho_FlrPAR = rho_FlrPAR
        self.rho_FlrNIR = rho_FlrNIR
        self.eta_GlobPAR = eta_GlobPAR

        # Inputs
        self.switch = 0.0  # Lamp on/off (0 or 1)
        self.LAI = 1.0     # Leaf Area Index

    def multilayer_tau_rho(self, tau_Can, tau_Flr, rho_Can, rho_Flr):
        tau = tau_Can * tau_Flr / (1 - rho_Can * rho_Flr)
        rho = rho_Can + tau_Can**2 * rho_Flr / (1 - rho_Can * rho_Flr)
        return tau, rho

    def compute(self):
        switch = self.switch

        # Power per area
        P = self.p_el if self.power_input else self.P_el / self.A
        W_el = P * self.A * switch

        # Radiation components
        R_PAR = 0.25 * P * switch
        R_NIR = 0.17 * P * switch
        R_IluAir_Glob = 0.58 * P * switch

        # NIR multilayer model
        tau_Can = np.exp(-self.K_NIR * self.LAI)
        rho_Can = self.rho_CanNIR * (1 - tau_Can)
        tau_CF_NIR, rho_CF_NIR = self.multilayer_tau_rho(
            tau_Can,
            1 - self.rho_FlrNIR,
            rho_Can,
            self.rho_FlrNIR
        )
        alpha_CanNIR = 1 - tau_CF_NIR - rho_CF_NIR
        alpha_FlrNIR = tau_CF_NIR

        # Canopy absorbed
        R_IluCan_PAR = R_PAR * (1 - self.rho_CanPAR) * (1 - np.exp(-self.K1_PAR * self.LAI))
        R_FlrCan_PAR = R_PAR * np.exp(-self.K1_PAR * self.LAI) * self.rho_FlrPAR * \
                       (1 - self.rho_CanPAR) * (1 - np.exp(-self.K2_PAR * self.LAI))
        R_IluCan_NIR = R_NIR * alpha_CanNIR
        R_IluCan_Glob = R_IluCan_PAR + R_FlrCan_PAR + R_IluCan_NIR

        # PAR absorbed in canopy (converted to umol/m²/s)
        R_PAR_Can = R_IluCan_PAR + R_FlrCan_PAR
        R_PAR_Can_umol = R_PAR_Can / 0.25 * self.eta_GlobPAR

        # Floor absorbed
        R_IluFlr_NIR = R_NIR * alpha_FlrNIR
        R_IluFlr_PAR = R_PAR * np.exp(-self.K1_PAR * self.LAI) * (1 - self.rho_FlrPAR)
        R_IluFlr_Glob = R_IluFlr_PAR + R_IluFlr_NIR

        return {
            "R_IluAir_Glob": R_IluAir_Glob,
            "R_IluCan_Glob": R_IluCan_Glob,
            "R_IluFlr_Glob": R_IluFlr_Glob,
            "R_PAR_Can_umol": R_PAR_Can_umol,
            "W_el": W_el
        }
