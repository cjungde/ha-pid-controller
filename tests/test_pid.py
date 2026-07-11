"""Unit tests for the pure PID core (no Home Assistant required)."""

import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "custom_components" / "pid_controller")
)

from pid import PIDController  # noqa: E402


def test_output_clamped_to_limits():
    pid = PIDController(kp=100, ki=0, kd=0, output_min=-5, output_max=5)
    # Huge positive error must clamp to output_max.
    out = pid.step(pv=0, setpoint=100, dt=1)
    assert out == 5.0
    # Huge negative error must clamp to output_min.
    pid.reset()
    out = pid.step(pv=100, setpoint=0, dt=1)
    assert out == -5.0


def test_integral_anti_windup_holds():
    pid = PIDController(kp=0, ki=1.0, kd=0, output_min=-5, output_max=5)
    # Drive it hard into saturation for many steps.
    for _ in range(100):
        pid.step(pv=0, setpoint=10, dt=1)
    # Integral must not exceed the output authority.
    assert pid.state.integral <= 5.0
    # Now flip the error; it should recover promptly, not after unwinding 100 steps.
    out = pid.step(pv=20, setpoint=10, dt=1)
    assert out < 5.0


def test_signed_output_negative_range():
    pid = PIDController(kp=1.0, ki=0, kd=0, output_min=-5, output_max=5)
    out = pid.step(pv=12, setpoint=10, dt=1)  # too warm -> negative shift
    assert out == -2.0


def test_i_only_converges_toward_setpoint():
    pid = PIDController(kp=0, ki=0.5, kd=0, output_min=-5, output_max=5)
    out = 0.0
    # Constant positive error accumulates integral over time.
    for _ in range(5):
        out = pid.step(pv=9, setpoint=10, dt=1)
    assert 0 < out <= 5.0


def test_feed_forward_ke():
    pid = PIDController(kp=0, ki=0, kd=0, ke=0.2, output_min=-10, output_max=10)
    # Colder outdoor -> larger feed-forward toward setpoint.
    out_cold = pid.step(pv=20, setpoint=20, dt=1, outdoor=-10)
    pid.reset()
    out_mild = pid.step(pv=20, setpoint=20, dt=1, outdoor=10)
    assert out_cold > out_mild


def test_derivative_on_measurement_no_setpoint_kick():
    pid = PIDController(kp=0, ki=0, kd=5.0, output_min=-10, output_max=10)
    pid.step(pv=20, setpoint=20, dt=1)  # prime last_pv
    # Setpoint jump with pv unchanged -> derivative term stays 0 (no kick).
    out = pid.step(pv=20, setpoint=25, dt=1)
    assert out == 0.0


if __name__ == "__main__":
    import traceback

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
