# Jungle Lab Studio - YAML DSL Reference

This document describes the YAML structure used for Jungle Lab Studio presets.

## Root Structure

A valid preset file must have a root `preset` object.

```yaml
preset:
  name: "My Preset"
  description: "A short description"
  author: "Author Name"
  version: "1.0.0"
  tags: ["tag1", "tag2"]
  settings:
    bpm: 120.0
    audio_reactive: true
    midi_enabled: true
  nodes: []  # List of nodes
  midi:      # Global MIDI mappings (optional)
    mappings: []
```

## Nodes

The `nodes` list contains definitions for all nodes in the graph.

```yaml
nodes:
  - id: "gen_particles_001"
    type: "particles"
    position: [100, 200]  # [x, y] canvas position
    
    # Parameters
    params:
      speed: 1.5
      count: 1000
      
      # Runtime Animations (attached to params)
      animate:
        speed:
          lfo:
            type: "sine"  # sine, square, triangle, noise
            freq: 0.5
            amp: 1.0
            offset: 0.0
            
    # Editor Animations (legacy/explicit list format)
    animations:
      - target: "speed"
        type: "lfo"
        frequency: 0.5
        waveform: "sine"
        amplitude: 1.0
        
    # Input Connections
    inputs:
      ctrl: "midi_listener_001"  # Connect 'ctrl' port to 'midi_listener_001' output
      
    # Triggers
    triggers:
      - type: "midi_note"
        note: 60
        channel: 1
        action:
          mode: "impulse"
          target: "count"
          amount: 500
          
    # Custom Node Data
    midi_mapping:  # Only for midi.listener
      message_type: "note_on"
      channel: 0
      note: 60
      
    target_generators: ["gen_particles_001"] # Only for midi.launcher
```

## Global MIDI Mappings

Alternative to node-specific triggers, allowing global mapping definition.

```yaml
midi:
  mappings:
    - trigger: "CC14"
      target: "nodes.gen_particles_001.params.speed"
    - trigger: "NOTE_60"
      target: "nodes.gen_particles_001.params.count"
```

## Parameter Types

- **Float/Int:** `speed: 1.0`
- **Boolean:** `active: true`
- **String:** `blend_mode: "mix"`
- **Color:** Not explicitly typed in YAML, usually broken down or handled as specific params.

## Node Types

See `NODE_REFERENCE.md` for a full list of available node types and their parameters.
