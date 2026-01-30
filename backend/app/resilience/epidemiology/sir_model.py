"""
SIR Burnout Epidemiology Model.

Applies compartmental epidemic modeling to burnout spread:
- S (Susceptible): Healthy residents at risk of burnout
- I (Infected): Residents currently experiencing burnout
- R (Recovered): Residents recovered or removed from system

Based on Kermack-McKendrick SIR model from infectious disease epidemiology.

dS/dt = -β * S * I / N
dI/dt = β * S * I / N - γ * I
dR/dt = γ * I

Where:
- β = transmission rate (burnout contagion through schedule pressure)
- γ = recovery rate (1/γ = average burnout duration)
- N = total population
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional

import numpy as np
from scipy.integrate import odeint


class SIRState(str, Enum):
    """Burnout state classification."""

    SUSCEPTIBLE = "susceptible"  # Healthy, at risk
    INFECTED = "infected"  # Currently burned out
    RECOVERED = "recovered"  # Recovered or removed


@dataclass
class SIRSnapshot:
    """Point-in-time SIR model state."""

    timestamp: datetime
    susceptible: int
    infected: int
    recovered: int
    total_population: int
    beta: float  # Transmission rate
    gamma: float  # Recovery rate
    r0: float  # Basic reproduction number (β/γ)


@dataclass
class SIRForecast:
    """SIR model forecast."""

    days_ahead: int
    forecasted_infected: list[int]
    forecasted_susceptible: list[int]
    forecasted_recovered: list[int]
    peak_infected: int
    peak_day: int
    time_to_peak: int
    total_cases: int  # Cumulative infected


class SIRModel:
    """
    SIR epidemic model for burnout spread.

    Models burnout as contagious through:
    - Schedule pressure cascades
    - Social contagion (team morale)
    - Workload redistribution (covering for burned-out colleagues)
    """

    def __init__(
        self,
        transmission_rate: float = 0.3,  # β - burnout contagion rate
        recovery_rate: float = 0.1,  # γ - recovery rate (1/10 = 10 days avg)
    ) -> None:
        """
        Initialize SIR model.

        Args:
            transmission_rate: β - probability susceptible becomes infected
            recovery_rate: γ - rate at which infected recover (1/duration)
        """
        self.beta = transmission_rate
        self.gamma = recovery_rate
        self.r0 = self.beta / self.gamma if self.gamma > 0 else 0.0

    @property
    def basic_reproduction_number(self) -> float:
        """
        Calculate R0 (basic reproduction number).

        R0 = β / γ

        Interpretation:
        - R0 < 1: Burnout will die out
        - R0 = 1: Endemic equilibrium
        - R0 > 1: Burnout epidemic will spread
        """
        return self.r0

    def simulate(
        self,
        initial_susceptible: int,
        initial_infected: int,
        initial_recovered: int,
        days: int = 90,
    ) -> SIRForecast:
        """
        Simulate SIR dynamics forward in time.

        Args:
            initial_susceptible: Initial susceptible count
            initial_infected: Initial infected (burned out) count
            initial_recovered: Initial recovered count
            days: Number of days to simulate

        Returns:
            SIRForecast with projected disease course
        """
        N = initial_susceptible + initial_infected + initial_recovered

        if N == 0:
            # Empty population
            return SIRForecast(
                days_ahead=days,
                forecasted_infected=[0] * days,
                forecasted_susceptible=[0] * days,
                forecasted_recovered=[0] * days,
                peak_infected=0,
                peak_day=0,
                time_to_peak=0,
                total_cases=0,
            )

            # Initial conditions [S, I, R]
        y0 = [initial_susceptible, initial_infected, initial_recovered]

        # Time vector
        t = np.linspace(0, days, days)

        # Solve ODE
        solution = odeint(self._sir_derivatives, y0, t, args=(N,))

        S, I, R = solution.T

        # Convert to integers
        susceptible = [int(s) for s in S]
        infected = [int(i) for i in I]
        recovered = [int(r) for r in R]

        # Find peak
        peak_infected = max(infected)
        peak_day = infected.index(peak_infected)
        time_to_peak = peak_day

        # Total cases (final recovered + current infected)
        total_cases = recovered[-1] + infected[-1]

        return SIRForecast(
            days_ahead=days,
            forecasted_infected=infected,
            forecasted_susceptible=susceptible,
            forecasted_recovered=recovered,
            peak_infected=peak_infected,
            peak_day=peak_day,
            time_to_peak=time_to_peak,
            total_cases=int(total_cases),
        )

    def _sir_derivatives(self, y, t, N):
        """
        Calculate SIR derivatives for ODE solver.

        Args:
            y: [S, I, R] current state
            t: Time
            N: Total population

        Returns:
            [dS/dt, dI/dt, dR/dt]
        """
        S, I, R = y

        dS_dt = -self.beta * S * I / N
        dI_dt = self.beta * S * I / N - self.gamma * I
        dR_dt = self.gamma * I

        return [dS_dt, dI_dt, dR_dt]

    def calculate_herd_immunity_threshold(self) -> float:
        """
        Calculate herd immunity threshold.

        HIT = 1 - 1/R0

        This is the fraction of population that must be "immune" (recovered)
        to stop burnout spread.

        Returns:
            Herd immunity threshold (0-1)
        """
        if self.r0 <= 1.0:
            return 0.0  # No epidemic, no herd immunity needed

        return 1.0 - 1.0 / self.r0

    def predict_final_size(self, initial_infected: int, total_population: int) -> int:
        """
        Predict final epidemic size (total who will become infected).

        Uses final size equation for SIR model.

        Args:
            initial_infected: Initial number infected
            total_population: Total population size

        Returns:
            Predicted total cases
        """
        if total_population == 0:
            return 0

            # Simulate to equilibrium
        forecast = self.simulate(
            initial_susceptible=total_population - initial_infected,
            initial_infected=initial_infected,
            initial_recovered=0,
            days=365,  # Long enough to reach equilibrium
        )

        return forecast.total_cases

    def calculate_intervention_effect(
        self,
        current_beta: float,
        intervention_beta: float,
        current_infected: int,
        total_population: int,
        days: int = 60,
    ) -> dict:
        """
        Calculate effect of intervention that reduces transmission.

        Args:
            current_beta: Current transmission rate
            intervention_beta: Reduced transmission rate after intervention
            current_infected: Current number infected
            total_population: Total population
            days: Forecast horizon

        Returns:
            Dict with before/after comparison
        """
        # Baseline (no intervention)
        baseline_model = SIRModel(
            transmission_rate=current_beta, recovery_rate=self.gamma
        )
        baseline_forecast = baseline_model.simulate(
            initial_susceptible=total_population - current_infected,
            initial_infected=current_infected,
            initial_recovered=0,
            days=days,
        )

        # With intervention
        intervention_model = SIRModel(
            transmission_rate=intervention_beta, recovery_rate=self.gamma
        )
        intervention_forecast = intervention_model.simulate(
            initial_susceptible=total_population - current_infected,
            initial_infected=current_infected,
            initial_recovered=0,
            days=days,
        )

        # Calculate impact
        cases_prevented = (
            baseline_forecast.total_cases - intervention_forecast.total_cases
        )
        peak_reduction = (
            baseline_forecast.peak_infected - intervention_forecast.peak_infected
        )
        peak_delay = intervention_forecast.time_to_peak - baseline_forecast.time_to_peak

        return {
            "baseline_total_cases": baseline_forecast.total_cases,
            "intervention_total_cases": intervention_forecast.total_cases,
            "cases_prevented": cases_prevented,
            "cases_prevented_pct": (
                cases_prevented / baseline_forecast.total_cases * 100
                if baseline_forecast.total_cases > 0
                else 0
            ),
            "baseline_peak": baseline_forecast.peak_infected,
            "intervention_peak": intervention_forecast.peak_infected,
            "peak_reduction": peak_reduction,
            "peak_delay_days": peak_delay,
            "baseline_r0": baseline_model.r0,
            "intervention_r0": intervention_model.r0,
        }

    def classify_epidemic_phase(
        self, infected_count: int, total_population: int
    ) -> str:
        """
        Classify current epidemic phase.

        Args:
            infected_count: Current infected count
            total_population: Total population

        Returns:
            Phase classification string
        """
        if total_population == 0:
            return "no_population"

        prevalence = infected_count / total_population

        if infected_count == 0:
            return "no_cases"
        elif prevalence < 0.01:
            return "sporadic"  # < 1%
        elif prevalence < 0.05:
            return "outbreak"  # 1-5%
        elif prevalence < 0.15:
            return "epidemic"  # 5-15%
        else:
            return "crisis"  # > 15%
