# Jungle Lab Studio - Node Reference

## Generators
Nodes that create visual content from scratch.

- **`shader`**: Generic shader generator.
  - Inputs: `texture` (optional), `ctrl` (optional)
  - Params: `shader_path` (str)
- **`particles`**: Particle system generator.
  - Inputs: `ctrl`
  - Params: `speed`, `count`, `size`, `color`
- **`generator.noise`**: Simplex/Perlin noise generator.
  - Params: `scale`, `detail`, `roughness`, `speed`
- **`generator.checkerboard`**: Checkerboard pattern.
  - Params: `rows`, `cols`, `color1`, `color2`

## Effects (VFX)
Nodes that process an input texture.

- **`effect.blur`**: Gaussian blur.
  - Params: `radius`, `direction` (horizontal/vertical/both)
- **`effect.glow`**: Basic glow/bloom.
  - Params: `threshold`, `intensity`, `radius`
- **`effect.advanced_bloom`**: High-performance, large-radius bloom.
  - Params: `threshold`, `intensity`, `radius` (multiplier), `smoothness`
- **`effect.feedback`**: Temporal feedback loop with transform.
  - Params: `amount` (decay), `zoom`, `rotation`, `offset_x`, `offset_y`
- **`effect.kaleidoscope`**: Kaleidoscope mirror effect.
  - Params: `segments`, `angle`, `zoom`, `center_x`, `center_y`
- **`effect.mirror`**: Simple axis mirroring.
  - Params: `mode` (horizontal/vertical/quad)
- **`effect.distort`**: UV distortion using noise or texture.
  - Params: `amount`, `speed`, `scale`
- **`effect.pixelate`**: Pixelation effect.
  - Params: `pixel_size`
- **`effect.edge_detect`**: Edge detection (Sobel).
  - Params: `sensitivity`, `thickness`, `color`
- **`effect.color_gradient`**: Map brightness to color gradient.
  - Params: `color1`, `color2`, `threshold`

## Compositing & Routing
Nodes for combining or routing signals.

- **`blend`**: Blend two textures.
  - Params: `opacity`, `mode` (0=Mix, 1=Add, 2=Mult, 3=Screen)
- **`composite`**: Advanced composite (similar to blend currently).
- **`math.operation`**: Arithmetic operations on textures.
  - Params: `operation` (0=Add, 1=Sub, 2=Mult, 3=Div, 4=Min, 5=Max, 6=Diff), `clamp_output`, `mix_factor`
- **`utility.buffer`**: Frame buffer for feedback loops (delays frame by 1).
  - Inputs: `input0`
  - Outputs: `output` (previous frame)

## MIDI & Control
Nodes for external control.

- **`midi.listener`**: Listens for specific MIDI message.
  - Params: `device_index`, `channel`, `normalize`, `smoothing`
  - State: Learns MIDI Note/CC.
- **`midi.launcher`**: Trigger/Gate logic for MIDI.
  - Params: `threshold`, `attack`, `release`, `mode` (Momentary/Toggle)

## Output
Terminal nodes.

- **`output`**: Main output.
- **`preview`**: Auxiliary preview output.
