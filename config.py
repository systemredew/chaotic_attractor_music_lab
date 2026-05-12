from __future__ import annotations

from dataclasses import dataclass


WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 980
MIN_WINDOW_HEIGHT = 680
VISUAL_PADDING = 44
FPS = 60
BACKGROUND_COLOR = (8, 10, 16)
TEXT_COLOR = (225, 230, 238)
MUTED_TEXT_COLOR = (145, 154, 171)
TRAIL_LIMIT = 5500
POINT_RADIUS = 3
PULSE_DECAY = 0.84
PULSE_RADIUS_BOOST = 18

UI_PANEL_HEIGHT = 450
UI_MARGIN = 14
UI_EDGE_MARGIN = 10
UI_PANEL_INSET = 18
UI_RADIUS = 6
UI_BACKGROUND_COLOR = (13, 18, 27)
UI_BACKGROUND_ALPHA = 188
UI_PANEL_COLOR = (24, 31, 44)
UI_PANEL_ALPHA = 235
UI_HOVER_COLOR = (35, 45, 62)
UI_ACTIVE_COLOR = (34, 75, 92)
UI_BORDER_COLOR = (73, 86, 108)
UI_ACCENT_COLOR = (98, 210, 190)

DEFAULT_DT = 0.01
DEFAULT_STEPS_PER_FRAME = 4
SIMULATION_SPEED_DIVISOR = 3.0
MIN_STEPS_PER_FRAME = 1
MAX_STEPS_PER_FRAME = 40
MIN_DENSITY_MULTIPLIER = 0.1
MAX_DENSITY_MULTIPLIER = 2.0
MIN_CHAOS_INFLUENCE = 0.0
MAX_CHAOS_INFLUENCE = 2.0
MIN_TRAIL_LIMIT = 500
MAX_TRAIL_LIMIT = 12000

MIDI_TICKS_PER_BEAT = 480
DEFAULT_TEMPO_BPM = 120
DEFAULT_CHANNEL = 0
DEFAULT_ROOT_NOTE = 48
MIN_ROOT_NOTE = 36
MAX_ROOT_NOTE = 72
DEFAULT_NOTE_DURATION = 0.22
MIN_NOTE_COOLDOWN = 0.045
MAX_NOTE_COOLDOWN = 0.65
MIN_CAMERA_ZOOM = 4.0
MAX_CAMERA_ZOOM = 20.0
MIN_CAMERA_ROTATION = -3.14
MAX_CAMERA_ROTATION = 3.14

LYAPUNOV_EPSILON = 1e-7
LYAPUNOV_RENORMALIZE_EVERY = 8
LYAPUNOV_WINDOW = 256

BIFURCATION_R_MIN = 2.5
BIFURCATION_R_MAX = 4.0
BIFURCATION_R_STEPS = 800
BIFURCATION_ITERATIONS = 450
BIFURCATION_WARMUP = 250
BIFURCATION_IMAGE = "bifurcation_logistic.png"

EXPORT_DIR = "exports"
DEFAULT_MIDI_FILE = "chaotic_attractor_session.mid"
DEFAULT_SCREENSHOT_FILE = "chaotic_attractor_screenshot.png"
APP_ID = "chaotic-attractor-music-lab"
APP_ICON_PNG = "assets/app_icon.png"
APP_ICON_ICO = "assets/app_icon.ico"

MIN_BPM = 40
MAX_BPM = 220
MIN_NOTE_LENGTH_MULTIPLIER = 0.25
MAX_NOTE_LENGTH_MULTIPLIER = 3.0
MIN_OCTAVE_RANGE = 1
MAX_OCTAVE_RANGE = 6
MIN_NOTE_PROBABILITY = 0.05
MAX_NOTE_PROBABILITY = 1.0
MIN_SWING = 0.0
MAX_SWING = 0.65
MIN_ECHO = 0.0
MAX_ECHO = 1.0

VISUAL_STYLES = ["aurora", "ember", "ice", "mono"]


@dataclass(frozen=True)
class ViewBounds:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float = -1.0
    z_max: float = 1.0


SYSTEM_BOUNDS: dict[str, ViewBounds] = {
    "Lorenz": ViewBounds(-30.0, 30.0, -35.0, 35.0, 0.0, 55.0),
    "Rossler": ViewBounds(-15.0, 15.0, -15.0, 15.0, 0.0, 30.0),
    "Henon": ViewBounds(-1.6, 1.6, -0.5, 0.5),
    "Logistic": ViewBounds(2.5, 4.0, 0.0, 1.0),
}

SYSTEM_PARAMETER_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    "Lorenz": {
        "sigma": (1.0, 30.0),
        "rho": (1.0, 60.0),
        "beta": (0.5, 8.0),
    },
    "Rossler": {
        "a": (0.01, 1.0),
        "b": (0.01, 1.0),
        "c": (1.0, 14.0),
    },
    "Henon": {
        "a": (0.5, 1.6),
        "b": (0.05, 0.45),
    },
    "Logistic": {
        "r": (2.5, 4.0),
        "r_step": (0.00005, 0.004),
    },
}
