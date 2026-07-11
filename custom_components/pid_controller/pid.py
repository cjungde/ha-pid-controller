"""Pure PID controller logic — no Home Assistant dependencies.

Design choices:
- Derivative on measurement (not on error) to avoid derivative kick when the
  setpoint changes.
- Clamping anti-windup: the integral term is only accumulated while the output
  is not saturated (integral hold), and the integral itself is clamped to the
  output limits. This is robust for the very slow thermal systems this module
  targets (underfloor heating, buffer tanks).
- Optional feed-forward term Ke * (setpoint - outdoor) for weather compensation.
- Signed output: output_min may be negative (e.g. -5..+5 K for a heating-curve
  shift), which the standard 0-100% PWM thermostats cannot express.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PIDState:
    """Serializable controller state (persist across restarts if desired)."""

    integral: float = 0.0
    last_pv: float | None = None
    # Last computed components, for debugging / dashboards.
    p: float = 0.0
    i: float = 0.0
    d: float = 0.0
    e: float = 0.0
    output: float = 0.0


class PIDController:
    """A positional-form PID controller with anti-windup and feed-forward."""

    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        output_min: float,
        output_max: float,
        ke: float = 0.0,
        invert: bool = False,
        state: PIDState | None = None,
    ) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.ke = ke
        self.output_min = output_min
        self.output_max = output_max
        self.invert = invert
        self.state = state or PIDState()

    def reset(self) -> None:
        """Clear integral and derivative history."""
        self.state = PIDState()

    def step(
        self,
        pv: float,
        setpoint: float,
        dt: float,
        outdoor: float | None = None,
    ) -> float:
        """Advance the controller by one time step.

        Args:
            pv: Process variable (measured value), e.g. mean room temperature.
            setpoint: Target value.
            dt: Elapsed time since the previous step, in seconds. Must be > 0.
            outdoor: Optional outdoor temperature for the Ke feed-forward term.

        Returns:
            The (clamped) controller output.
        """
        if dt <= 0:
            # No time elapsed — return the last output unchanged.
            return self.state.output

        error = setpoint - pv
        if self.invert:
            error = -error

        # Proportional
        p = self.kp * error

        # Derivative on measurement (guard against the first call)
        if self.state.last_pv is None:
            d = 0.0
        else:
            d_pv = (pv - self.state.last_pv) / dt
            d = -self.kd * d_pv
            if self.invert:
                d = -d
        self.state.last_pv = pv

        # Feed-forward (weather compensation): pushes output up as it gets colder
        e = 0.0
        if self.ke and outdoor is not None:
            e = self.ke * (setpoint - outdoor)
            if self.invert:
                e = -e

        # Tentative integral (will be committed only if not saturating)
        candidate_integral = self.state.integral + self.ki * error * dt
        # Clamp integral to output range so it can never wind up beyond authority
        candidate_integral = _clamp(candidate_integral, self.output_min, self.output_max)

        output_unclamped = p + candidate_integral + d + e
        output = _clamp(output_unclamped, self.output_min, self.output_max)

        # Anti-windup (integral hold): only keep the new integral if the output
        # is not saturated, or if the integral change pulls the output back
        # toward the valid range.
        saturated_high = output_unclamped > self.output_max
        saturated_low = output_unclamped < self.output_min
        if (saturated_high and error > 0) or (saturated_low and error < 0):
            # Would push further into saturation — freeze the integral.
            pass
        else:
            self.state.integral = candidate_integral

        # Record components for debugging
        self.state.p = p
        self.state.i = self.state.integral
        self.state.d = d
        self.state.e = e
        self.state.output = output
        return output


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
