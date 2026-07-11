"""Constants for the PID Controller integration."""

DOMAIN = "pid_controller"

# Config / options keys
CONF_NAME = "name"
CONF_INPUT_ENTITY = "input_entity"          # process variable (measured)
CONF_SETPOINT_ENTITY = "setpoint_entity"    # optional: setpoint from an entity
CONF_SETPOINT_VALUE = "setpoint_value"      # fallback fixed setpoint
CONF_OUTPUT_ENTITY = "output_entity"        # target number entity to write
CONF_OUTDOOR_ENTITY = "outdoor_entity"      # optional: for Ke feed-forward
CONF_KP = "kp"
CONF_KI = "ki"
CONF_KD = "kd"
CONF_KE = "ke"
CONF_OUTPUT_MIN = "output_min"
CONF_OUTPUT_MAX = "output_max"
CONF_SAMPLE_TIME = "sample_time_s"
CONF_INVERT = "invert"

# Defaults tuned for slow underfloor-heating / heating-curve-shift use.
DEFAULT_KP = 0.0
DEFAULT_KI = 0.3
DEFAULT_KD = 0.0
DEFAULT_KE = 0.0
DEFAULT_OUTPUT_MIN = -5.0
DEFAULT_OUTPUT_MAX = 5.0
DEFAULT_SETPOINT = 0.0
DEFAULT_SAMPLE_TIME = 3600  # seconds (1 h) — appropriate for FBH thermal mass
DEFAULT_INVERT = False

# Persisted runtime keys
DATA_COORDINATOR = "coordinator"

# Storage (persists integral / last_pv / enabled across restarts)
STORAGE_VERSION = 1

PLATFORMS = ["sensor", "switch"]
