"""
Burnout Epidemiology Module.

Applies infectious disease epidemiology models to burnout spread prediction
in medical residency programs. Treats burnout as a "contagious" condition
that propagates through social and work networks.

Core Components:
    SIRModel: Kermack-McKendrick compartmental epidemic model (S-I-R)
    SIRState: Burnout state classification (susceptible/infected/recovered)
    RtCalculator: Real-time effective reproduction number estimation (Cori method)

Key Concepts:
    R0 (Basic Reproduction Number): Average secondary cases per primary case.
        R0 > 1 means epidemic growth, R0 < 1 means decline.
    Rt (Effective Reproduction Number): R0 adjusted for current immunity.
    Herd Immunity Threshold: HIT = 1 - 1/R0, fraction needed for containment.
    Serial Interval: Time between successive cases in transmission chain.

Scientific Basis:
    Kermack & McKendrick (1927): SIR model foundations
    Cori et al. (2013): EpiEstim real-time Rt estimation
    Christakis & Fowler (2008): Social contagion of emotions
    Bakker et al. (2009): Burnout contagion in healthcare

Example:
    >>> from app.resilience.epidemiology import SIRModel, RtCalculator
    >>> model = SIRModel(transmission_rate=0.3, recovery_rate=0.1)
    >>> print(f"R0 = {model.basic_reproduction_number}")  # R0 = 3.0
    >>> forecast = model.simulate(95, 5, 0, days=90)
    >>> print(f"Peak: {forecast.peak_infected} on day {forecast.peak_day}")

See README.md in this directory for full documentation.
"""

from app.resilience.epidemiology.sir_model import SIRModel, SIRState
from app.resilience.epidemiology.rt_calculator import RtCalculator

__all__ = [
    "SIRModel",
    "SIRState",
    "RtCalculator",
]
