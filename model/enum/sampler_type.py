from enum import Enum


class Sampler(str, Enum):
    """
    Enumeração de samplers suportados.
    """
    DPM_2 = "DPM_2"
    DPM_2_KARRAS = "DPM_2_KARRAS"
    DPM_2_A = "DPM_2_A"
    DPM_2_A_KARRAS = "DPM_2_A_KARRAS"
    DPM_2_M = "DPM_2_M"
    DPM_2_M_KARRAS = "DPM_2_M_KARRAS"
    DPM_2_M_SDE_KARRAS = "DPM_2_M_SDE_KARRAS"
    EULER = "EULER"
    EULER_A = "EULER_A"
    HEUN = "HEUN"
    LMS = "LMS"
