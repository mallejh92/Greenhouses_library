import math

class Solar_model:
    def __init__(self,
                 A,
                 I_glob,
                 SC=0,
                 LAI=1,
                 eta_glob_air=0.1,
                 K1_PAR=0.7,
                 K2_PAR=0.7,
                 K_NIR=0.27,
                 rho_CanPAR=0.07,
                 rho_CanNIR=0.35,
                 rho_FlrPAR=0.07,
                 rho_FlrNIR=0.07,
                 tau_RfPAR=0.85,
                 rho_RfPAR=0.13,
                 tau_RfNIR=0.85,
                 rho_RfNIR=0.13,
                 tau_thScrPAR=0.6,
                 rho_thScrPAR=0.35,
                 tau_thScrNIR=0.6,
                 rho_thScrNIR=0.35,
                 eta_glob_PAR=0.5,
                 eta_glob_NIR=0.5,
                 eta_GlobPAR=2.3):
        self.A = A
        self.I_glob = I_glob
        self.SC = SC
        self.LAI = LAI
        self.eta_glob_air = eta_glob_air
        self.K1_PAR = K1_PAR
        self.K2_PAR = K2_PAR
        self.K_NIR = K_NIR
        self.rho_CanPAR = rho_CanPAR
        self.rho_CanNIR = rho_CanNIR
        self.rho_FlrPAR = rho_FlrPAR
        self.rho_FlrNIR = rho_FlrNIR
        self.tau_RfPAR = tau_RfPAR
        self.rho_RfPAR = rho_RfPAR
        self.tau_RfNIR = tau_RfNIR
        self.rho_RfNIR = rho_RfNIR
        self.tau_thScrPAR = tau_thScrPAR
        self.rho_thScrPAR = rho_thScrPAR
        self.tau_thScrNIR = tau_thScrNIR
        self.rho_thScrNIR = rho_thScrNIR
        self.eta_glob_PAR = eta_glob_PAR
        self.eta_glob_NIR = eta_glob_NIR
        self.eta_GlobPAR = eta_GlobPAR

        # Initialize output variables
        self.R_SunCov_Glob = 0.0
        self.P_SunCov_Glob = 0.0
        self.R_SunCan_Glob = 0.0
        self.P_SunCan_Glob = 0.0
        self.R_SunFlr_Glob = 0.0
        self.P_SunFlr_Glob = 0.0
        self.R_SunAir_Glob = 0.0
        self.P_SunAir_Glob = 0.0
        self.R_PAR_Can_umol = 0.0
        self.R_t_Glob = 0.0

    def multi_layer_tau_rho(self, tau1, tau2, rho1, rho2):
        tau_total = tau1 * tau2 / (1 - rho1 * rho2)
        rho_total = rho1 + (tau1**2 * rho2 / (1 - rho1 * rho2))
        return tau_total, rho_total

    def step(self, dt):
        """
        Advance the simulation by one time step
        
        Parameters:
        -----------
        dt : float
            Time step [s]
        """
        results = self.compute()
        
        # Update class attributes with computed values
        self.R_SunCov_Glob = results["R_SunCov_Glob"]
        self.P_SunCov_Glob = results["P_SunCov_Glob"]
        self.R_SunCan_Glob = results["R_SunCan_Glob"]
        self.P_SunCan_Glob = results["P_SunCan_Glob"]
        self.R_SunFlr_Glob = results["R_SunFlr_Glob"]
        self.P_SunFlr_Glob = results["P_SunFlr_Glob"]
        self.R_SunAir_Glob = results["R_SunAir_Glob"]
        self.P_SunAir_Glob = results["P_SunAir_Glob"]
        self.R_PAR_Can_umol = results["R_PAR_Can_umol"]

    def compute(self):
        tau_ML_covPAR, rho_ML_covPAR = self.multi_layer_tau_rho(
            self.tau_RfPAR, self.tau_thScrPAR, self.rho_RfPAR, self.rho_thScrPAR)
        tau_ML_covNIR, rho_ML_covNIR = self.multi_layer_tau_rho(
            self.tau_RfNIR, self.tau_thScrNIR, self.rho_RfNIR, self.rho_thScrNIR)

        tau_covPAR = (1 - self.SC) * self.tau_RfPAR + self.SC * tau_ML_covPAR
        rho_covPAR = (1 - self.SC) * self.rho_RfPAR + self.SC * rho_ML_covPAR
        tau_covNIR = (1 - self.SC) * self.tau_RfNIR + self.SC * tau_ML_covNIR
        rho_covNIR = (1 - self.SC) * self.rho_RfNIR + self.SC * rho_ML_covNIR

        alpha_covPAR = 1 - tau_covPAR - rho_covPAR
        alpha_covNIR = 1 - tau_covNIR - rho_covNIR

        R_SunCov_Glob = (alpha_covPAR * self.eta_glob_PAR + alpha_covNIR * self.eta_glob_NIR) * self.I_glob
        P_SunCov_Glob = R_SunCov_Glob * self.A

        R_t_PAR = self.I_glob * self.eta_glob_PAR * tau_covPAR * (1 - self.eta_glob_air)
        R_NIR = self.I_glob * self.eta_glob_NIR * (1 - self.eta_glob_air)

        tau_CF_NIR, rho_CF_NIR = self.multi_layer_tau_rho(
            math.exp(-self.K_NIR * self.LAI), 1 - self.rho_FlrNIR,
            self.rho_CanNIR * (1 - math.exp(-self.K_NIR * self.LAI)), self.rho_FlrNIR)

        tau_CCF_NIR, rho_CCF_NIR = self.multi_layer_tau_rho(
            tau_covNIR, tau_CF_NIR, rho_covNIR, rho_CF_NIR)

        alpha_FlrNIR = tau_CCF_NIR
        alpha_CanNIR = 1 - tau_CCF_NIR - rho_CCF_NIR

        R_SunCan_PAR = R_t_PAR * (1 - self.rho_CanPAR) * (1 - math.exp(-self.K1_PAR * self.LAI))
        R_FlrCan_PAR = R_t_PAR * math.exp(-self.K1_PAR * self.LAI) * self.rho_FlrPAR * (1 - self.rho_CanPAR) * (1 - math.exp(-self.K2_PAR * self.LAI))
        R_SunCan_NIR = R_NIR * alpha_CanNIR
        R_PAR_Can = R_SunCan_PAR + R_FlrCan_PAR
        R_PAR_Can_umol = R_PAR_Can / self.eta_glob_PAR * self.eta_GlobPAR
        R_SunCan_Glob = R_SunCan_PAR + R_FlrCan_PAR + R_SunCan_NIR
        P_SunCan_Glob = R_SunCan_Glob * self.A

        R_SunFlr_PAR = R_t_PAR * math.exp(-self.K1_PAR * self.LAI) * (1 - self.rho_FlrPAR)
        R_SunFlr_NIR = R_NIR * alpha_FlrNIR
        R_SunFlr_Glob = R_SunFlr_PAR + R_SunFlr_NIR
        P_SunFlr_Glob = R_SunFlr_Glob * self.A

        R_SunAir_Glob = self.eta_glob_air * self.I_glob * (tau_covPAR * self.eta_glob_PAR + (alpha_CanNIR + alpha_FlrNIR) * self.eta_glob_NIR)
        P_SunAir_Glob = R_SunAir_Glob * self.A

        # Calculate total transmitted radiation above the canopy
        self.R_t_Glob = self.I_glob * (1 - self.eta_glob_air) * (self.eta_glob_PAR * tau_covPAR + self.eta_glob_NIR * (alpha_CanNIR + alpha_FlrNIR))

        return {
            "R_SunCov_Glob": R_SunCov_Glob,
            "P_SunCov_Glob": P_SunCov_Glob,
            "R_SunCan_Glob": R_SunCan_Glob,
            "P_SunCan_Glob": P_SunCan_Glob,
            "R_SunFlr_Glob": R_SunFlr_Glob,
            "P_SunFlr_Glob": P_SunFlr_Glob,
            "R_SunAir_Glob": R_SunAir_Glob,
            "P_SunAir_Glob": P_SunAir_Glob,
            "R_PAR_Can_umol": R_PAR_Can_umol
        }


