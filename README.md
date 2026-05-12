# Chaotic Attractor Music Lab

Generative music and visualization laboratory for chaotic dynamical systems in Python.

## Short Description

Chaotic Attractor Music Lab simulates Lorenz, Rossler, Henon, and Logistic systems, draws their trajectories with pygame, estimates chaotic behavior, and maps coordinates, speed, acceleration, curvature, Lyapunov values, and bifurcation movement into quantized MIDI notes.

Chaos here is not treated as random noise. The app turns deterministic mathematical motion into constrained musical material: scales, root notes, velocity ranges, cooldowns, and rhythmic density keep the output musical while the systems provide variation.

## Demo Placeholder

Run the app, select a preset with `1`-`5`, and export the current session with `S`.

## Features

- Lorenz and Rossler continuous attractors integrated with RK4.
- Henon and Logistic discrete maps.
- Logistic bifurcation sequencer where `r` moves from order toward chaos.
- Realtime pygame visualization with projected 3D trajectories.
- Mouse-driven pygame control panel for presets, transport, export, chaos mode, speed, density, tone, scale, trail length, and system parameters.
- Interactive pseudo-3D camera for all systems, including Henon and Logistic/Bifurcation embeddings: drag the scene to rotate, use the mouse wheel to zoom, or enable automatic camera rotation.
- Resizable window and fullscreen mode.
- Performance mode hides the control panel and leaves a clean stage view.
- Multi-voice music mode adds bass, harmony, or percussion layers depending on the selected system.
- System parameter sliders let you reshape Lorenz, Rossler, Henon, and Logistic behavior during runtime.
- Depth shading for 3D trails.
- MIDI note mapping with major, minor, pentatonic, whole-tone, and chromatic scales.
- Live MIDI output when a MIDI device is available.
- pygame audio fallback when live MIDI is unavailable.
- MIDI file export.
- Approximate Lyapunov exponent estimation.
- Logistic bifurcation diagram export via matplotlib.
- Presets for calm, chaotic, drone, percussive, and bifurcation-driven behavior.
- Minimal pytest suite.

## Installation

```bash
cd chaotic_attractor_music_lab
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

On Linux or macOS, activate with:

```bash
source .venv/bin/activate
```

`python-rtmidi` is used by `mido` for live MIDI ports. If it is hard to install on a machine, the app still exports MIDI files and tries a pygame-generated tone fallback.

## Usage

```bash
python main.py
```

Quick non-interactive check:

```bash
python main.py --smoke
```

Run tests:

```bash
python -m pytest
```

## Controls

Most keyboard controls are also available in the translucent bottom GUI panel. Use the sliders to change simulation speed, music density, tone, chaos influence, trail length, musical timing, and system parameters. Drag the visual scene with the left mouse button to rotate the 3D camera, hold the mouse wheel to pan the scene, and use the mouse wheel to zoom.

- `SPACE` pause or resume.
- `R` reset current system.
- `1` Calm Lorenz.
- `2` Butterfly Chaos.
- `3` Rossler Drone.
- `4` Henon Percussion.
- `5` Bifurcation Piano.
- `M` mute or unmute.
- `S` export MIDI to `exports/chaotic_attractor_session.mid`.
- `B` generate Logistic bifurcation diagram PNG in `exports/`.
- `UP` and `DOWN` change simulation speed.
- `LEFT` and `RIGHT` change musical density.
- `C` enable or disable chaos influence.
- `F11` or `Alt+Enter` toggle fullscreen.
- `ESC` exit.

GUI-only controls:

- `Scale` cycles through available musical scales.
- `Auto Cam` toggles automatic camera rotation.
- `Style` cycles visual palettes.
- `Voice` toggles multi-voice music mapping.
- `Perf` toggles performance mode.
- `Default` restores the current preset and global controls to default values.
- `Tone` changes the base MIDI note.
- `Chaos influence` controls how strongly the Lyapunov estimate affects note density.
- `Trail` changes the number of retained trajectory points.
- `BPM`, `Length`, `Octaves`, `Probability`, and `Swing` shape the generated music.
- Dynamic parameter sliders edit the active system parameters, such as Lorenz `sigma/rho/beta` or Rossler `a/b/c`.

## Presets

- Calm Lorenz: lower `rho`, minor pentatonic scale, slow ambient note density.
- Butterfly Chaos: classic Lorenz parameters, natural minor scale, more active musical behavior.
- Rossler Drone: Rossler attractor with harmonic minor, longer and calmer gestures.
- Henon Percussion: discrete Henon map with whole-tone color and short events.
- Bifurcation Piano: Logistic map sequencer, moving from stable behavior toward chaos.

## Project Structure

```text
chaotic_attractor_music_lab/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── systems/
├── math_core/
├── music/
├── visual/
├── presets/
└── tests/
```

`systems/` owns equations and state. `math_core/` owns numerical methods and analysis. `music/` owns note mapping, MIDI, and audio fallback. `visual/` owns pygame rendering, camera projection, colors, and overlay. `presets/` describes reusable app states.

## Mathematical Background

A dynamical system describes how a state evolves. The state can be a point in phase space: for Lorenz, phase space is `(x, y, z)`; for Logistic, it is a single value `x` plus a changing parameter `r`.

An attractor is a region of phase space toward which trajectories tend to evolve. In chaotic systems, this region can have intricate structure: the motion is bounded and patterned, but highly sensitive to initial conditions.

Chaos does not mean randomness. Lorenz and Rossler are deterministic: the same initial state and parameters produce the same future. They are chaotic because nearby starting points can separate exponentially, making long-term prediction difficult.

## Lorenz System Explanation

The Lorenz attractor is defined by:

```text
dx/dt = sigma(y - x)
dy/dt = x(rho - z) - y
dz/dt = xy - beta z
```

The default classic parameters are `sigma=10`, `rho=28`, and `beta=8/3`. The trajectory forms the well-known butterfly-like attractor. In this project, `x` affects pitch, `y` affects velocity, and `z` affects octave placement.

## Rossler System Explanation

The Rossler system is:

```text
dx/dt = -y - z
dy/dt = x + ay
dz/dt = b + z(x - c)
```

With `a=0.2`, `b=0.2`, and `c=5.7`, it produces a spiraling attractor. It is useful for drone-like music because the trajectory often feels smoother than Lorenz while still being chaotic.

## Henon Map Explanation

The Henon map is discrete:

```text
x[n+1] = 1 - a*x[n]^2 + y[n]
y[n+1] = b*x[n]
```

It updates by iteration, not by a time-step ODE integrator. The abrupt point-to-point jumps make it useful for percussive musical mapping.

## Logistic Map Explanation

The Logistic map is:

```text
x[n+1] = r*x[n]*(1 - x[n])
```

As `r` increases from about `2.5` to `4.0`, the system moves from stable fixed points through period doubling and into chaotic behavior. The app uses this as a bifurcation sequencer: `r` controls harmonic tension and rhythmic density, while `x` controls pitch.

## Numerical Integration

Continuous systems need numerical integration because their equations describe derivatives rather than direct next states. The project includes Euler and fourth-order Runge-Kutta methods in `math_core/integrators.py`.

Euler is simple and fast but less accurate. RK4 evaluates the derivative several times per step, giving a much better approximation for attractor visualization and music timing.

## Runge-Kutta Method

RK4 estimates the next state from four derivative samples:

```text
k1 = f(x)
k2 = f(x + dt*k1/2)
k3 = f(x + dt*k2/2)
k4 = f(x + dt*k3)
next = x + dt*(k1 + 2k2 + 2k3 + k4)/6
```

This reduces numerical drift and keeps the simulated attractor more stable than plain Euler for the same `dt`.

## Lyapunov Exponent

The Lyapunov estimator evolves two nearby trajectories. If their distance tends to shrink, the estimate is negative. If it stays roughly neutral, it is near zero. If it grows, the estimate is positive and indicates chaos.

The app uses this value musically:

- lower values produce calmer and sparser note events;
- middle values increase activity;
- higher values make events denser and more unstable.

## Bifurcation Diagram

The Logistic bifurcation diagram samples many `r` values. For each `r`, the system iterates, discards warmup points, and stores the remaining `x` values. Press `B` to save a PNG diagram.

Bifurcations become rhythm by changing subdivision and density. Stable regions produce steadier pulses; chaotic regions produce quicker and more active note decisions.

## Music Mapping

The mapper is deterministic and scale-aware:

- `x coordinate -> pitch`
- `y coordinate -> fuzz/distortion amount in the pygame audio fallback`
- `z coordinate -> octave`
- `speed -> note energy`
- `acceleration -> accent`
- `curvature -> dissonance/density`
- `Lyapunov exponent -> chaos intensity`
- `Logistic r -> harmonic tension`
- `bifurcation events -> rhythm subdivision`

Notes are quantized to named scales from `music/scales.py`, so the output remains musical instead of becoming unfiltered randomness.

## MIDI Export

Every played note is stored as a `NoteEvent`. Press `S` to export the captured session to:

```text
exports/chaotic_attractor_session.mid
```

The MIDI file can be opened in any DAW or notation program.

## Future Improvements

- Add editable parameter sliders in the pygame UI.
- Add multiple MIDI channels and instrument programs.
- Add synchronized drum tracks from bifurcation events.
- Add OSC output for external visual tools.
- Add recording to WAV.
- Add richer Lyapunov spectrum estimation.
- Add GPU-accelerated rendering for longer trails.
- Add preset serialization to JSON or TOML.
