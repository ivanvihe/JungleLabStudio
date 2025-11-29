import threading
import time
from collections import deque
from typing import Callable, Deque, List, Optional, Tuple

import mido


class MidiInput:
    def __init__(self, device: Optional[str] = None):
        self.device = device
        self.port: Optional[mido.ports.BaseInput] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.listeners: List[Callable[[mido.Message], None]] = []
        self.queue: Deque[mido.Message] = deque(maxlen=64)

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def add_listener(self, callback: Callable[[mido.Message], None]) -> None:
        if callback not in self.listeners:
            self.listeners.append(callback)

    def remove_listener(self, callback: Callable[[mido.Message], None]) -> None:
        if callback in self.listeners:
            self.listeners.remove(callback)

    def _loop(self) -> None:
        while self.running:
            try:
                # If device is None, try to find the first available one or wait
                target_device = self.device
                if not target_device:
                    devices = self.list_devices()
                    if devices:
                        target_device = devices[0]
                    else:
                        time.sleep(1.0)
                        continue

                print(f"MIDI: Connecting to {target_device}...")
                with mido.open_input(target_device) as port:
                    self.port = port
                    print(f"MIDI: Connected to {target_device}")
                    
                    # Message loop
                    while self.running:
                        # Poll for messages with a small timeout to check 'running' flag
                        # but mido's iteration blocks. We use port.poll() or iterate.
                        # Standard iteration is blocking, so we can't easily break unless we close port.
                        # But we can set a callback on the port or just iterate.
                        for msg in port:
                            self.queue.append(msg)
                            for listener in self.listeners:
                                try:
                                    listener(msg)
                                except Exception as e:
                                    print(f"MIDI Listener Error: {e}")
                            
                            if not self.running:
                                break
                        
                        # If loop exits but we are still running, it means device disconnected
                        if self.running:
                            print("MIDI: Device disconnected, retrying...")
                            time.sleep(2.0)
                            break
            except Exception as e:
                print(f"MIDI Error: {e}")
                time.sleep(2.0)

    def consume(self) -> Tuple[mido.Message, ...]:
        items = tuple(self.queue)
        self.queue.clear()
        return items

    def stop(self) -> None:
        self.running = False
        if self.port:
            try:
                self.port.close()
            except Exception:
                pass
        self.port = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

    def set_device(self, device_name: str) -> None:
        self.device = device_name
        # Trigger reconnection by closing current port if open
        if self.port:
            self.port.close()

    @staticmethod
    def list_devices() -> Tuple[str, ...]:
        try:
            return tuple(mido.get_input_names())
        except Exception:
            return ()
