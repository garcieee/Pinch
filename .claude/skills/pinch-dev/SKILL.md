---
name: pinch-dev
description: Reference for developing Pinch, the gesture-based AR cropping tool. Use whenever working on this codebase — implementing build phases, adding gestures, touching state.py/cards.py/overlay.py/gestures.py, or making any visual/HUD changes. Encodes the architecture rules, gesture vocabulary, state machine, and FUI design spec that all changes must follow.
---

# Pinch — Gesture-Based AR Cropping Tool

A Python desktop app that turns the webcam feed into an interactive AR space.
Users crop regions of the live feed with hand gestures; captures become
physical-feeling card objects in the scene — grabbed, moved, resized, rotated,
thrown — entirely with the hands. **No keyboard, no mouse.**

## Stack

- Python 3.11+
- opencv-python (capture, window, all drawing)
- mediapipe (hand landmarks)
- No GUI framework — all UI drawn directly onto the OpenCV frame

## Architecture rules (hard constraints)

```
camera.py    ←  webcam capture, frame loop
gestures.py  ←  landmarks → gesture classification (pure)
crop.py      ←  frame + bbox → cropped image (pure)
overlay.py   ←  HUD, crop rect, reticles, flash (pure)
cards.py     ←  card rendering, hand hit-testing, transform math (pure)
physics.py   ←  card momentum, friction, throw velocity (pure)
state.py     ←  state shape + update_state reducer (pure)
main.py      ←  orchestrator — the only multi-module importer
```

- **Functional programming throughout** — pure functions, no classes.
- **One central immutable state dict**, updated via a single
  `update_state(state, event) -> new_state` reducer in `state.py`.
- **Each module is blind to the others** — only `main.py` imports across
  modules. Modules import only stdlib or third-party packages.
- Drawing: only `cv2.line`, `cv2.rectangle`, `cv2.putText`, `cv2.circle`.
  Numpy compositing allowed only for shutter flash blend and card rotation
  (warpAffine). Pure functions: take frame + state, return new frame.

## Gesture vocabulary

| Gesture | Context | Action |
|---|---|---|
| Finger-frame (both hands, thumb + index extended) | SNAP | Draw live crop box |
| Dual pinch (both hands pinch while framing) | SNAP | Capture → shutter flash → card spawns |
| Open palm held 1.0s (5 fingers, one hand) | Any | Toggle SNAP ↔ PLAY |
| Single pinch over a card | PLAY | Grab card — follows pinch midpoint |
| Pinch release | PLAY | Drop card (inherits velocity → slides with friction) |
| Two hands pinching same card | PLAY | Scale (pinch distance) + rotate (pinch angle) |
| Quick flick while grabbing | PLAY | Throw — momentum, bounces off frame edges |
| Closed fist held over card 1.0s | PLAY | Crush — card deleted |
| Both fists held 2.0s | PLAY | PURGE ALL — countdown, then clear all cards |

Rules:
- Every hold gesture shows a visible countdown ring/label while charging.
- Mode toggle and purge require deliberate holds to prevent accidental triggers.
- Hysteresis on pinch detection (separate engage/release thresholds) to prevent flicker.

## State machine

```
MODE: SNAP | PLAY        (palm-hold toggles)

SNAP:  idle → framing → locked → capture → idle
PLAY:  idle → hover → grab → drag → release
                    ↘ two-hand grab → transform (scale/rotate) → release
                    ↘ fist-hover → crush-charging → deleted

GLOBAL: dual-fist hold → purge-charging → purge all
```

State additions: `mode`, `held_card_id`, `gesture_charge` (0–1 progress for
hold gestures), per-card `velocity`, `scale`, `rotation`.

## Visual / FUI design spec

Style: analog instrument / FUI (Blade Runner 2049 screen graphics) —
utilitarian, limited palette, aerospace instrumentation. No gradients, no
blur, no rounded corners, no shadows, no icons. Typography and 1px lines only.

### Palette (BGR for OpenCV) — no other colors, ever

| Role | Hex | BGR |
|---|---|---|
| Background | `#0A0A0A` | `(10, 10, 10)` |
| Amber — active / values | `#E8A33D` | `(61, 163, 232)` |
| Warm gray — labels / keys | `#5A5852` | `(82, 88, 90)` |
| Mid gray — reticles | `#7A7770` | `(112, 119, 122)` |
| Inactive border | `#3A3935` | `(53, 57, 58)` |
| Red — destructive only | `#C84B31` | `(49, 75, 200)` |

### Typography

- `cv2.FONT_HERSHEY_PLAIN`, small scale.
- ALL CAPS. KEY in warm gray, VALUE in amber.
- Zero-padded numbers: `0461 × 0288`, `CAP.001`, `00:04:12:08`.

### HUD zones

- Top-left: `GCROP_v0.1` (amber) / `CAM.00 — 1280×0720 — 30.00FPS` (gray)
- Top-right (right-aligned, keys gray / values amber):
  `HANDS 02/02`, `MODE SNAP|PLAY` (flashes once on toggle), `STATE FRAMING`
- Bottom-left: `TC 00:04:12:08 · CAPS 002`
- Bottom-right — gesture legend (context-sensitive, fades in with hands
  detected, out after 3s idle):
  - SNAP: `FRAME=CROP · 2×PINCH=CAPTURE · PALM=PLAY`
  - PLAY: `PINCH=GRAB · FIST=CRUSH · PALM=SNAP`
- Ruler ticks on top/bottom edges: major every 80px (6px), minor at
  16/32/48/64px offsets (3px), dim gray.

### Hold-gesture charge indicator

- Thin amber arc around the gesturing hand, sweeping 0→360° over hold duration.
- Label: `PLAY IN 00.6s` / `CRUSH 00.4s` / `PURGE 01.2s` (red for destructive).
- Cancels and fades instantly if the gesture breaks.

### Crop region (SNAP framing)

- 1px rectangle; amber when stable, mid gray when unstable.
- Corner crosshairs: `+` marks, 18px arms extending past the corner.
- Dimension label above top-right corner, amber, zero-padded.
- Stability countdown below bottom-left: `LOCK IN 00.4s` in gray.

### Fingertip markers

- Thumb tip + index tip only; crosshair + 12px circle, mid gray.
- In PLAY mode, the reticle over a hovered card turns amber.

### Capture cards

- Hard rectangles, zero border-radius, 4px padding, bg `#0A0A0A`.
- Header: `CAP.001` left / timestamp `14:02:11` right — amber.
- Footer: `LABEL · .96` left, gray; no `[X]` button — deletion is gestural.
- Grabbed/hovered: amber border. Idle: `#3A3935` border.
- Spawn at crop location, drift to resting spot over ~10 frames. No spawn rotation.
- Runtime `scale` (0.4×–2.5× clamp) and free `rotation` from two-hand transform.
- Thrown cards bounce off frame edges with 0.6 restitution; friction decays
  velocity per frame.
- Crush animation: collapse to center over 6 frames, then a 1-frame red tick mark.

### Shutter flash

- Single-frame white flash at 40% opacity, decaying 10%/frame over 4 frames.

## Build phases

Phases 1–2 complete (camera + HUD baseline, MediaPipe fingertip tracking).

3. SNAP mode: framing classification + live crop rectangle + stability lock
4. Dual-pinch capture + shutter flash + card spawn
5. Mode system: palm-hold toggle, HUD mode readout, gesture legend per mode
6. PLAY mode core: pinch-grab, drag, release with hand hit-testing
7. Physics: throw momentum, friction, edge bounce (`physics.py`)
8. Two-hand transform: scale + rotate grabbed card
9. Destruction: fist-crush single card, dual-fist purge all, charge indicators
10. (optional) Scene intelligence: async object labeling on captured cards

Keyboard keys exist only as debug fallbacks and are never required for normal use.
