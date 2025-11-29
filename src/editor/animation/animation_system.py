"""
AnimationSystem - Manages parameter animations (LFO, Envelope, etc.)
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from core.graph.node import LFO, Envelope
from editor.graph.visual_node import AnimationBlock
import math
import random


@dataclass
class ActiveAnimation:
    """Active animation instance tracking"""
    node_id: str
    param_name: str
    animation_block: AnimationBlock
    lfo: Optional[LFO] = None
    envelope: Optional[Envelope] = None
    current_value: float = 0.0


class AnimationSystem:
    """
    Manages all parameter animations in the visual graph
    """

    def __init__(self):
        self.active_animations: Dict[str, ActiveAnimation] = {}  # key: f"{node_id}.{param_name}"
        self.time: float = 0.0

    def add_animation(self, node_id: str, param_name: str, animation_block: AnimationBlock):
        """Register a new animation for a parameter"""
        key = f"{node_id}.{param_name}"

        # Create animation instance
        anim = ActiveAnimation(
            node_id=node_id,
            param_name=param_name,
            animation_block=animation_block
        )

        # Initialize based on animation type
        if animation_block.animation_type == "lfo":
            anim.lfo = LFO(
                type=animation_block.lfo_waveform,
                freq=animation_block.lfo_frequency,
                amp=animation_block.lfo_amplitude,
                phase=animation_block.lfo_phase
            )
        elif animation_block.animation_type == "envelope":
            anim.envelope = Envelope(
                attack=animation_block.envelope_attack,
                decay=animation_block.envelope_decay,
                sustain=animation_block.envelope_sustain,
                release=animation_block.envelope_release
            )

        self.active_animations[key] = anim

    def remove_animation(self, node_id: str, param_name: str):
        """Remove an animation"""
        key = f"{node_id}.{param_name}"
        if key in self.active_animations:
            del self.active_animations[key]

    def get_animation(self, node_id: str, param_name: str) -> Optional[ActiveAnimation]:
        """Get active animation for a parameter"""
        key = f"{node_id}.{param_name}"
        return self.active_animations.get(key)

    def trigger_envelope(self, node_id: str, param_name: str):
        """Trigger an envelope animation"""
        key = f"{node_id}.{param_name}"
        anim = self.active_animations.get(key)

        if anim and anim.envelope:
            anim.envelope.trigger()

    def release_envelope(self, node_id: str, param_name: str):
        """Release an envelope animation"""
        key = f"{node_id}.{param_name}"
        anim = self.active_animations.get(key)

        if anim and anim.envelope:
            anim.envelope.release_trigger()

    def update(self, dt: float) -> Dict[str, Dict[str, float]]:
        """
        Update all animations and return parameter values

        Returns:
            Dict[node_id, Dict[param_name, value]]
        """
        self.time += dt
        param_values: Dict[str, Dict[str, float]] = {}

        for key, anim in self.active_animations.items():
            if not anim.animation_block.is_active:
                continue

            value = 0.0

            # Calculate animation value
            if anim.animation_block.animation_type == "lfo" and anim.lfo:
                value = anim.lfo.update(dt)
                # Apply offset
                value += anim.animation_block.lfo_offset

            elif anim.animation_block.animation_type == "envelope" and anim.envelope:
                value = anim.envelope.update(dt)

            elif anim.animation_block.animation_type == "noise_walk":
                value = self._noise_walk(anim, dt)

            elif anim.animation_block.animation_type == "keyframe":
                value = self._keyframe_animation(anim, self.time)

            # Store value
            anim.current_value = value

            # Build result dict
            if anim.node_id not in param_values:
                param_values[anim.node_id] = {}

            param_values[anim.node_id][anim.param_name] = value

        return param_values

    def _noise_walk(self, anim: ActiveAnimation, dt: float) -> float:
        """Perlin-like noise walk animation"""
        block = anim.animation_block

        # Simple Perlin-like noise using sine waves
        t = self.time * block.noise_speed
        value = 0.0
        amplitude = 1.0
        frequency = 1.0

        for _ in range(block.noise_octaves):
            value += amplitude * math.sin(t * frequency * 6.28318)
            amplitude *= 0.5
            frequency *= 2.0

        return value * block.noise_scale

    def _keyframe_animation(self, anim: ActiveAnimation, time: float) -> float:
        """Keyframe-based animation"""
        keyframes = anim.animation_block.keyframes

        if not keyframes or len(keyframes) < 2:
            return 0.0

        # Sort keyframes by time
        sorted_keyframes = sorted(keyframes, key=lambda kf: kf.get("time", 0.0))

        # Find surrounding keyframes
        for i in range(len(sorted_keyframes) - 1):
            kf1 = sorted_keyframes[i]
            kf2 = sorted_keyframes[i + 1]

            t1 = kf1.get("time", 0.0)
            t2 = kf2.get("time", 0.0)
            v1 = kf1.get("value", 0.0)
            v2 = kf2.get("value", 0.0)

            if t1 <= time <= t2:
                # Linear interpolation
                if t2 - t1 > 0:
                    alpha = (time - t1) / (t2 - t1)
                    return v1 + (v2 - v1) * alpha
                else:
                    return v1

        # Before first or after last keyframe
        if time < sorted_keyframes[0].get("time", 0.0):
            return sorted_keyframes[0].get("value", 0.0)
        else:
            return sorted_keyframes[-1].get("value", 0.0)

    def clear(self):
        """Clear all animations"""
        self.active_animations.clear()
        self.time = 0.0

    def get_animation_count(self) -> int:
        """Get number of active animations"""
        return len(self.active_animations)

    def get_animations_for_node(self, node_id: str) -> List[ActiveAnimation]:
        """Get all animations for a specific node"""
        return [anim for anim in self.active_animations.values() if anim.node_id == node_id]

    def sync_from_visual_graph(self, visual_graph):
        """Synchronize animations from a VisualGraph"""
        # Clear existing
        self.clear()

        # Add all animations from nodes
        for node in visual_graph.nodes.values():
            for anim_block in node.animations:
                if anim_block.is_active:
                    self.add_animation(node.id, anim_block.target_param, anim_block)
