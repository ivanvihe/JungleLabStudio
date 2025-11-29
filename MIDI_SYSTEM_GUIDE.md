# MIDI Control System - User Guide

## Overview

JungleLabStudio now includes a comprehensive MIDI control system that allows you to create interactive visual performances using MIDI controllers (pads, knobs, faders, keyboards, etc.).

The system follows a simple flow:

```
MIDI Listener → Launcher → Generator → Preview/Output
```

## Node Types

### 1. MIDI Listener Node (`midi.listener`)

**Purpose:** Captures MIDI events in real-time and outputs values (0-1 or 0-127).

**Features:**
- **MIDI Learn Mode**: Click "Learn" to automatically detect and map MIDI controls
- Auto-detection of MIDI controls (notes, CC messages)
- Displays current value and activity indicator
- Device selection
- Configurable smoothing

**Parameters:**
- `device_index` (0-16): Select MIDI device
- `normalize` (0/1):
  - 1 = Output 0-1 range (normalized)
  - 0 = Output 0-127 range (raw)
- `smoothing` (0-1): Value smoothing amount (0 = instant, 1 = very smooth)

**Visual Feedback:**
- Horizontal bar shows current value
- Green pulse indicates MIDI activity
- Text display shows mapped control (e.g., "CC 7 Ch 1" or "Note 60 Ch 10")

**Usage:**
1. Add MIDI Listener node to canvas
2. Click "MIDI Learn" button in inspector
3. Move/press a control on your MIDI controller
4. Listener automatically captures the control mapping

---

### 2. Launcher Node (`midi.launcher`)

**Purpose:** Processes MIDI signals and activates/modulates generators.

**Features:**
- Multiple activation types
- Configurable threshold and timing
- Modulation curves
- Range mapping
- Visual feedback

**Activation Types:**

#### 0: On/Off (Trigger)
Simple boolean trigger - activates when input crosses threshold.

Use cases:
- Trigger visual effects with pads
- On/off toggle for generators

Parameters:
- `threshold`: Activation level (default: 0.5)
- `hold_time`: How long to stay active after trigger

#### 1: Range
Maps input range to output range continuously.

Use cases:
- Control parameter values with knobs/faders
- Smooth transitions

Parameters:
- `input_min` / `input_max`: Input range to map from
- `output_min` / `output_max`: Output range to map to
- `curve`: Modulation curve (linear/exponential/logarithmic/smooth_step)

#### 2: Velocity
Velocity-sensitive response (like MIDI note velocity).

Use cases:
- Velocity-sensitive visual responses
- Dynamic intensity control

Parameters:
- `threshold`: Minimum velocity to activate

#### 3: Toggle
Toggles state on each trigger.

Use cases:
- Switch between two states
- Enable/disable effects

**Common Parameters:**
- `activation_type` (0-3): Select activation mode
- `threshold` (0-1): Activation threshold
- `ramp_time` (0-5s): Transition time
- `hold_time` (0-10s): Hold time before release
- `curve` (0-3): Modulation curve type
- `invert` (0/1): Invert output value

**Visual Feedback:**
- Left bar: Input value from MIDI listener
- Orange line: Threshold indicator
- Right bar: Output value (green when active)
- Pulsing glow when active

---

## Connection Flow

### Basic Setup

1. **Add Nodes:**
   - Add a MIDI Listener node
   - Add a Launcher node
   - Add a Generator node
   - Add Preview/Output node

2. **Connect Nodes:**
   ```
   MIDI Listener.output → Launcher.midi_value
   Launcher.output → Generator.parameters
   Generator.output → Preview/Output.input
   ```

3. **Configure MIDI Listener:**
   - Click "MIDI Learn"
   - Move a control on your MIDI controller
   - Listener captures the mapping

4. **Configure Launcher:**
   - Select activation type
   - Adjust threshold, ramp time, etc.
   - Set output range

5. **Configure Generator:**
   - In YAML, add animation block with MIDI mapping
   - Or use visual editor to map launcher to parameters

---

## Parameter Modulation

### YAML Format

To modulate a parameter via MIDI in YAML presets:

```yaml
nodes:
  - id: my_generator
    type: generator.noise
    params:
      scale: 5.0
      speed: 1.0
      # other params...
      animate:
        speed:  # Parameter to modulate
          midi:
            launcher: launcher_001  # Launcher node ID
            scale: 5.0  # Multiply launcher output by this
            offset: 0.0  # Add this offset
            curve: linear  # Curve type
```

### Multiple Parameter Mappings

One launcher can control multiple parameters:

```yaml
animate:
  speed:
    midi:
      launcher: launcher_001
      scale: 3.0
  scale:
    midi:
      launcher: launcher_001
      scale: 10.0
      offset: 5.0
```

---

## Use Cases & Examples

### Example 1: Basic Knob Control

**Setup:** Control noise pattern speed with a MIDI knob

```
MIDI Listener (CC 1) → Launcher (Range Mode) → Noise Generator (speed param)
```

**Configuration:**
- Listener: Learn to CC 1
- Launcher:
  - activation_type: 1 (Range)
  - output_min: 0.0
  - output_max: 5.0
- Generator: Animate `speed` parameter

**Result:** Turning knob smoothly controls animation speed from 0 to 5x

---

### Example 2: Pad Triggers

**Setup:** Trigger different generators with MIDI pads

```
Pad 1 Listener → Launcher (On/Off) → Checkerboard Generator
Pad 2 Listener → Launcher (On/Off) → Noise Generator
Both → Blend → Output
```

**Configuration:**
- Each listener learns a different pad (e.g., Note 36, 37)
- Launchers in On/Off mode with quick ramp times
- Generators activate/deactivate based on pad presses

**Result:** Performance-ready visual triggering system

---

### Example 3: Velocity-Sensitive Effects

**Setup:** Control effect intensity based on note velocity

```
MIDI Listener (Notes) → Launcher (Velocity Mode) → Distortion Effect (amount param)
```

**Configuration:**
- Listener: Learn to a note range
- Launcher:
  - activation_type: 2 (Velocity)
  - output_max: 1.0
- Effect: Modulate `amount` parameter

**Result:** Harder hits = stronger distortion

---

### Example 4: Multi-Control Performance

**Setup:** Complex performance with multiple MIDI controls

```
CC 1 Listener → Launcher → Noise.speed
CC 2 Listener → Launcher → Distort.amount
CC 7 Listener → Launcher → Color.hue
Pad Listener → Launcher → Transform.rotate

All → Composite → Output
```

**Result:** Full performance rig with multiple simultaneous controls

---

## Tips & Best Practices

### 1. MIDI Learn Workflow
- Always use MIDI Learn for quick mapping
- Test each control immediately after learning
- Save presets with MIDI mappings for reuse

### 2. Smoothing
- Use higher smoothing (0.2-0.5) for knobs/faders
- Use low smoothing (0.0-0.1) for pads/triggers
- Adjust based on visual response desired

### 3. Ramp Times
- Quick ramps (0.05-0.1s) for punchy triggers
- Slow ramps (0.5-2s) for smooth transitions
- Zero ramp for instant response

### 4. Threshold Settings
- Set threshold around 0.1-0.3 for sensitive pads
- Set threshold around 0.5 for deliberate triggers
- Test with actual controller to find sweet spot

### 5. Output Ranges
- Use output_max > 1.0 to amplify effects
- Use output_min > 0.0 to prevent full "off" state
- Experiment with ranges for best visual impact

### 6. Curve Types
- **Linear**: Natural, direct control
- **Exponential**: Slow start, fast end (good for builds)
- **Logarithmic**: Fast start, slow end (good for decays)
- **Smooth Step**: S-curve, smooth transitions

---

## Troubleshooting

### MIDI Not Responding
1. Check MIDI device is connected
2. Verify device shows in MIDI device list
3. Try MIDI Learn again
4. Check console for MIDI messages

### Unexpected Values
1. Check normalize setting (0-1 vs 0-127)
2. Verify input/output ranges in launcher
3. Check for inverted output
4. Review modulation curve settings

### Laggy Response
1. Reduce smoothing value
2. Reduce ramp_time
3. Use lower-latency MIDI interface if available

### Mapping Not Saved
1. Ensure you save the preset after mapping
2. Check YAML file includes MIDI mappings section
3. Verify launcher connections are saved

---

## Advanced Topics

### Custom Modulation Curves
You can add custom curves by editing the MIDIModulationManager class in `src/core/midi_modulation.py`.

### Multiple Launchers to One Generator
You can have multiple launchers control different parameters of the same generator for complex modulation setups.

### MIDI Feedback (Future)
Future versions will support MIDI output for controller feedback (LED rings, etc.).

---

## Keyboard Shortcuts

- **Ctrl + L**: Toggle MIDI Learn mode (when MIDI Listener selected)
- **M**: Show/hide MIDI monitor
- **F1**: MIDI device configuration

---

## Example Presets

Check these presets for inspiration:

- `presets/templates/midi_example.yaml` - Basic MIDI control setup
- `presets/templates/midi_trigger_example.yaml` - Performance triggering setup

---

## API Reference

### MIDI Listener Node
```yaml
- id: listener_id
  type: midi.listener
  params:
    device_index: 0.0
    normalize: 1.0
    smoothing: 0.2
```

### Launcher Node
```yaml
- id: launcher_id
  type: midi.launcher
  params:
    activation_type: 1.0  # 0=On/Off, 1=Range, 2=Velocity, 3=Toggle
    threshold: 0.5
    ramp_time: 0.3
    hold_time: 0.0
    input_min: 0.0
    input_max: 1.0
    output_min: 0.0
    output_max: 1.0
    curve: 0.0  # 0=Linear, 1=Exp, 2=Log, 3=SmoothStep
    invert: 0.0
  inputs:
    midi_value: listener_id
```

### MIDI Modulation
```yaml
params:
  parameter_name: base_value
  animate:
    parameter_name:
      midi:
        launcher: launcher_id
        scale: 1.0
        offset: 0.0
        curve: linear
```

---

## Support

For issues, questions, or feature requests:
- GitHub: [JungleLabStudio Issues](https://github.com/ivanvihe/junglelab/issues)
- Documentation: See `/docs` folder

---

**Happy performing!** 🎹🎨
