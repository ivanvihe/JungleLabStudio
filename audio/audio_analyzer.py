import numpy as np
import logging
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from collections import deque

# Fallback AudioAnalyzer that doesn't require pyaudio
class AudioAnalyzer(QObject):
    """Audio analyzer for real-time FFT analysis - Fallback version without pyaudio"""
    
    audio_data_ready = pyqtSignal(np.ndarray)  # Raw audio data
    fft_data_ready = pyqtSignal(np.ndarray)    # FFT magnitude data
    level_changed = pyqtSignal(float)          # Overall audio level (0-100)
    
    def __init__(self, sample_rate=44100, chunk_size=1024, channels=1):
        super().__init__()
        
        # Audio parameters
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        
        # Data buffers
        self.audio_buffer = np.zeros(chunk_size, dtype=np.float32)
        self.fft_buffer = np.zeros(chunk_size // 2, dtype=np.float32)
        
        # Analysis parameters
        self.window = np.hanning(chunk_size)  # Hanning window for FFT
        self.fft_smooth_factor = 0.3  # Smoothing factor for FFT data
        self.level_smooth_factor = 0.1  # Smoothing factor for level
        
        # State variables
        self.is_running = False
        self.current_level = 0.0
        self.peak_level = 0.0
        self.last_fft = np.zeros(chunk_size // 2)
        
        # Device info
        self.input_device_index = None
        self.available_devices = []
        
        # Simulation timer for demo purposes
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self._generate_demo_data)
        self.demo_time = 0.0
        
        logging.info("Audio analyzer initialized (demo mode)")

    def get_available_devices(self):
        """Get list of available audio input devices (demo)"""
        self.available_devices = [
            {'index': 0, 'name': 'Demo Device 1', 'channels': 2, 'sample_rate': 44100},
            {'index': 1, 'name': 'Demo Device 2', 'channels': 1, 'sample_rate': 48000},
        ]
        return self.available_devices

    def set_input_device(self, device_index):
        """Set the audio input device (demo)"""
        if device_index is None or device_index < 0:
            self.input_device_index = None
            return False
        
        if device_index < len(self.available_devices):
            self.input_device_index = device_index
            logging.info(f"Set input device to demo device {device_index}")
            return True
        return False

    def start_analysis(self):
        """Start audio analysis (demo mode)"""
        if self.is_running:
            return True
            
        try:
            self.is_running = True
            self.demo_timer.start(50)  # 20 FPS
            logging.info("Audio analysis started (demo mode)")
            return True
        except Exception as e:
            logging.error(f"Failed to start audio analysis: {e}")
            return False

    def stop_analysis(self):
        """Stop audio analysis"""
        if not self.is_running:
            return
            
        try:
            self.is_running = False
            self.demo_timer.stop()
            logging.info("Audio analysis stopped")
        except Exception as e:
            logging.error(f"Error stopping audio analysis: {e}")

    def _generate_demo_data(self):
        """Generate demo audio data for visualization"""
        try:
            self.demo_time += 0.05
            
            # Generate demo audio signal
            t = np.linspace(0, 1, self.chunk_size)
            
            # Mix of different frequencies
            signal = (0.3 * np.sin(2 * np.pi * 60 * t + self.demo_time) +  # Bass
                     0.2 * np.sin(2 * np.pi * 200 * t + self.demo_time * 1.5) +  # Low-mid
                     0.2 * np.sin(2 * np.pi * 800 * t + self.demo_time * 0.8) +  # Mid
                     0.1 * np.sin(2 * np.pi * 3000 * t + self.demo_time * 2) +  # High-mid
                     0.1 * np.sin(2 * np.pi * 8000 * t + self.demo_time * 1.2))  # Treble
            
            # Add some variation
            envelope = 0.5 + 0.3 * np.sin(self.demo_time * 0.5)
            signal *= envelope
            
            # Store in buffer
            self.audio_buffer = signal.astype(np.float32)
            
            # Calculate level
            level = np.sqrt(np.mean(signal ** 2)) * 100
            self.current_level = (self.current_level * (1 - self.level_smooth_factor) + 
                                level * self.level_smooth_factor)
            
            # Perform FFT
            self._analyze_fft(signal)
            
            # Emit signals
            self.audio_data_ready.emit(self.audio_buffer)
            self.level_changed.emit(self.current_level)
            
        except Exception as e:
            logging.error(f"Error generating demo data: {e}")

    def _analyze_fft(self, audio_data):
        """Perform FFT analysis on audio data"""
        try:
            # Apply window function
            windowed_data = audio_data * self.window
            
            # Perform FFT
            fft_data = np.fft.rfft(windowed_data)
            
            # Calculate magnitude
            magnitude = np.abs(fft_data)
            
            # Convert to dB scale
            magnitude_db = 20 * np.log10(magnitude + 1e-10)
            
            # Normalize to 0-100 range
            magnitude_normalized = np.clip((magnitude_db + 60) / 60 * 100, 0, 100)
            
            # Apply smoothing
            self.last_fft = (self.last_fft * (1 - self.fft_smooth_factor) + 
                           magnitude_normalized * self.fft_smooth_factor)
            
            # Store in buffer
            self.fft_buffer = self.last_fft.copy()
            
            # Emit FFT data
            self.fft_data_ready.emit(self.fft_buffer)
            
        except Exception as e:
            logging.error(f"Error in FFT analysis: {e}")

    def get_frequency_bands(self, num_bands=5):
        """Get frequency band data for visualization"""
        if len(self.fft_buffer) == 0:
            return np.zeros(num_bands)
            
        try:
            # Calculate frequency resolution
            freq_resolution = self.sample_rate / (2 * len(self.fft_buffer))
            
            # Define frequency bands (logarithmic spacing)
            freq_bands = np.logspace(1, 4, num_bands + 1)  # 10 Hz to 10 kHz
            band_values = np.zeros(num_bands)
            
            for i in range(num_bands):
                start_freq = freq_bands[i]
                end_freq = freq_bands[i + 1]
                
                start_bin = int(start_freq / freq_resolution)
                end_bin = int(end_freq / freq_resolution)
                
                # Ensure bins are within range
                start_bin = max(0, min(start_bin, len(self.fft_buffer) - 1))
                end_bin = max(start_bin + 1, min(end_bin, len(self.fft_buffer)))
                
                # Average the magnitude in this frequency band
                if end_bin > start_bin:
                    band_values[i] = np.mean(self.fft_buffer[start_bin:end_bin])
                    
            return band_values
            
        except Exception as e:
            logging.error(f"Error calculating frequency bands: {e}")
            return np.zeros(num_bands)

    def get_bass_mid_treble(self):
        """Get simplified bass, mid, treble levels"""
        if len(self.fft_buffer) == 0:
            return {"bass": 0, "mid": 0, "treble": 0}
            
        try:
            freq_resolution = self.sample_rate / (2 * len(self.fft_buffer))
            
            # Define frequency ranges
            bass_range = (20, 250)      # Bass: 20-250 Hz
            mid_range = (250, 4000)     # Mid: 250-4000 Hz
            treble_range = (4000, 20000) # Treble: 4-20 kHz
            
            def get_range_level(freq_range):
                start_bin = int(freq_range[0] / freq_resolution)
                end_bin = int(freq_range[1] / freq_resolution)
                start_bin = max(0, min(start_bin, len(self.fft_buffer) - 1))
                end_bin = max(start_bin + 1, min(end_bin, len(self.fft_buffer)))
                
                if end_bin > start_bin:
                    return np.mean(self.fft_buffer[start_bin:end_bin])
                return 0
            
            return {
                "bass": get_range_level(bass_range),
                "mid": get_range_level(mid_range),
                "treble": get_range_level(treble_range)
            }
            
        except Exception as e:
            logging.error(f"Error calculating bass/mid/treble: {e}")
            return {"bass": 0, "mid": 0, "treble": 0}

    def get_current_level(self):
        """Get current audio level (0-100)"""
        return self.current_level

    def get_peak_level(self):
        """Get peak audio level (0-100)"""
        return self.peak_level

    def reset_peak(self):
        """Reset peak level"""
        self.peak_level = 0.0

    def get_fft_data(self):
        """Get current FFT data"""
        return self.fft_buffer.copy()

    def get_audio_data(self):
        """Get current audio data"""
        return self.audio_buffer.copy()

    def is_active(self):
        """Check if audio analysis is active"""
        return self.is_running

    def get_device_info(self):
        """Get current device information"""
        if self.input_device_index is not None and self.input_device_index < len(self.available_devices):
            return self.available_devices[self.input_device_index]
        return None

    def set_smoothing(self, fft_smooth=None, level_smooth=None):
        """Set smoothing factors"""
        if fft_smooth is not None:
            self.fft_smooth_factor = np.clip(fft_smooth, 0.0, 1.0)
        if level_smooth is not None:
            self.level_smooth_factor = np.clip(level_smooth, 0.0, 1.0)

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_analysis()
            logging.info("Audio analyzer cleaned up")
        except Exception as e:
            logging.error(f"Error cleaning up audio analyzer: {e}")

    def __del__(self):
        """Destructor"""
        self.cleanup()


# Try to import pyaudio and create full version if available
try:
    import pyaudio
    
    class AudioAnalyzerWithPyAudio(AudioAnalyzer):
        """Full audio analyzer with pyaudio support"""
        
        def __init__(self, sample_rate=44100, chunk_size=1024, channels=1):
            super().__init__(sample_rate, chunk_size, channels)
            
            # PyAudio specific
            self.format = pyaudio.paFloat32
            self.audio = None
            self.stream = None
            
            # Initialize PyAudio
            self.initialize_audio()

        def initialize_audio(self):
            """Initialize PyAudio and get available devices"""
            try:
                self.audio = pyaudio.PyAudio()
                self.get_available_devices()
                logging.info("Audio analyzer initialized with PyAudio")
            except Exception as e:
                logging.error(f"Failed to initialize PyAudio: {e}")
                self.audio = None

        def get_available_devices(self):
            """Get list of available audio input devices"""
            self.available_devices = []
            
            if not self.audio:
                return super().get_available_devices()  # Fallback to demo devices
                
            try:
                for i in range(self.audio.get_device_count()):
                    device_info = self.audio.get_device_info_by_index(i)
                    if device_info['maxInputChannels'] > 0:  # Has input channels
                        self.available_devices.append({
                            'index': i,
                            'name': device_info['name'],
                            'channels': device_info['maxInputChannels'],
                            'sample_rate': device_info['defaultSampleRate']
                        })
                logging.info(f"Found {len(self.available_devices)} audio input devices")
            except Exception as e:
                logging.error(f"Error getting audio devices: {e}")
                return super().get_available_devices()  # Fallback to demo devices
                
            return self.available_devices

        def start_analysis(self):
            """Start audio analysis with real audio input"""
            if self.is_running:
                return True
                
            if not self.audio:
                logging.warning("PyAudio not available, using demo mode")
                return super().start_analysis()  # Fallback to demo mode
                
            try:
                # Open audio stream
                self.stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=self.input_device_index,
                    frames_per_buffer=self.chunk_size,
                    stream_callback=self._audio_callback
                )
                
                self.stream.start_stream()
                self.is_running = True
                logging.info("Audio analysis started with real audio input")
                return True
                
            except Exception as e:
                logging.error(f"Failed to start audio analysis: {e}")
                logging.warning("Falling back to demo mode")
                return super().start_analysis()  # Fallback to demo mode

        def _audio_callback(self, in_data, frame_count, time_info, status):
            """Audio stream callback"""
            try:
                # Convert audio data to numpy array
                audio_data = np.frombuffer(in_data, dtype=np.float32)
                
                if len(audio_data) == self.chunk_size:
                    # Store in buffer
                    self.audio_buffer = audio_data.copy()
                    
                    # Calculate audio level
                    level = np.sqrt(np.mean(audio_data ** 2)) * 100
                    self.current_level = (self.current_level * (1 - self.level_smooth_factor) + 
                                        level * self.level_smooth_factor)
                    
                    # Update peak level
                    if level > self.peak_level:
                        self.peak_level = level
                    else:
                        self.peak_level *= 0.99  # Slow decay
                    
                    # Perform FFT analysis
                    self._analyze_fft(audio_data)
                    
                    # Emit signals
                    self.audio_data_ready.emit(self.audio_buffer)
                    self.level_changed.emit(self.current_level)
                    
            except Exception as e:
                logging.error(f"Error in audio callback: {e}")
                
            return (None, pyaudio.paContinue)

        def stop_analysis(self):
            """Stop audio analysis"""
            if not self.is_running:
                return
                
            try:
                self.is_running = False
                
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
                    self.stream = None
                    
                if hasattr(self, 'demo_timer'):
                    self.demo_timer.stop()
                    
                logging.info("Audio analysis stopped")
                
            except Exception as e:
                logging.error(f"Error stopping audio analysis: {e}")

        def cleanup(self):
            """Cleanup resources"""
            try:
                self.stop_analysis()
                if self.audio:
                    self.audio.terminate()
                    self.audio = None
                logging.info("Audio analyzer with PyAudio cleaned up")
            except Exception as e:
                logging.error(f"Error cleaning up audio analyzer: {e}")

    # Use the full version if pyaudio is available
    AudioAnalyzer = AudioAnalyzerWithPyAudio
    logging.info("Using AudioAnalyzer with PyAudio support")

except ImportError:
    logging.warning("PyAudio not available, using demo AudioAnalyzer")
    # AudioAnalyzer is already defined above as the fallback version