from OpenGL.GL import *
import numpy as np
import ctypes
import time
import math
import os
import logging

# Text rendering via PIL (optional). If not available, labels are skipped gracefully
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

from visuals.base_visualizer import BaseVisualizer
try:
    # Provided in visuals/__init__.py so it can be imported from presets
    from visuals import AudioAnalyzer
except Exception:
    AudioAnalyzer = None


class ScientificAudioAnalyzerVisualizer(BaseVisualizer):
    """
    Scientific-looking audio analyzer HUD inspired by lab/sonogram dashboards.
    Panels drawn with GL lines/triangles; metrics derived from FFT + audio buffer.

    Layout (NDC coordinates):
    ┌────────────────────────────────────────────────────────────────────────┐
    │ [A] SPREAD–ENTROPY (scatter)           [B] SPECTROGRAM (scrolling)     │
    │                                                                          │
    │ [C] Centroid/Spread/Flatness bars      [D] AM modulation strip chart    │
    │                                                                          │
    │                 Footer mini-bars + TONAL / NOISY indicator              │
    └────────────────────────────────────────────────────────────────────────┘
    """

    visual_name = "Scientific Analyzer"

    # ---------------------- lifecycle ----------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # GL handles
        self.color_prog = None
        self.tex_prog = None  # for label textures

        self.vao = None
        self.vbo = None  # dynamic for colored prims (pos2 + color4)

        # text label cache {label: (tex_id, w, h)}
        self.textures = {}

        # spectrogram texture
        self.spec_tex = None
        self.spec_w = 256
        self.spec_h = 256
        self.spec_row = 0

        # analyzer & data
        self.analyzer = None
        self.sample_rate = 44100
        self.fft = np.zeros(513, dtype=np.float32)
        self.prev_fft = None
        self.audio_chunk = np.zeros(1024, dtype=np.float32)
        self.level = 0.0

        # metrics history
        self.entropy_hist = np.zeros(240, dtype=np.float32)
        self.spread_hist = np.zeros(240, dtype=np.float32)
        self.centroid_hist = np.zeros(240, dtype=np.float32)
        self.am_hist = np.zeros(240, dtype=np.float32)
        self.hist_pos = 0

        # UI params
        self.theme = 0
        self.alpha = 0.95
        self.line_width = 1.0
        self.fft_smooth = 0.35

        # timing
        self._last = time.time()

    # ---------------------- GL setup ----------------------
    def initializeGL(self):
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0.0, 0.0, 0.0, 0.0)

        # compile shaders
        self.color_prog = self._build_color_program()
        self.tex_prog = self._build_tex_program()

        # basic VAO/VBO for colored primitives (pos2 + rgba)
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        stride = (2 + 4) * 4
        glBufferData(GL_ARRAY_BUFFER, 1024 * stride, None, GL_DYNAMIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))
        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        # spectrogram texture init
        self._init_spectrogram()

        # static labels
        self._build_label("SPREAD–ENTROPY SPACE", 20)
        self._build_label("SPECTROGRAM", 18)
        self._build_label("SPECTRAL SPREAD", 14)
        self._build_label("SPECTRAL FLATNESS", 14)
        self._build_label("SPECTRAL CENTROID", 14)
        self._build_label("AMPLITUDE MODULATION", 14)
        self._build_label("TONAL", 12)
        self._build_label("NOISY", 12)

        # analyzer
        try:
            if AudioAnalyzer is not None:
                self.analyzer = AudioAnalyzer()
                self.analyzer.set_smoothing(fft_smooth=self.fft_smooth, level_smooth=0.15)
                self.analyzer.start_analysis()
                self.sample_rate = self.analyzer.sample_rate
        except Exception as e:
            logging.error(f"AudioAnalyzer init failed: {e}")
            self.analyzer = None

    def resizeGL(self, w, h):
        glViewport(0, 0, max(1, w), max(1, h))

    def cleanup(self):
        try:
            if self.analyzer:
                self.analyzer.cleanup()
        except Exception:
            pass
        try:
            if self.spec_tex:
                glDeleteTextures([self.spec_tex])
                self.spec_tex = None
            if self.vbo:
                glDeleteBuffers(1, [self.vbo])
                self.vbo = None
            if self.vao:
                glDeleteVertexArrays(1, [self.vao])
                self.vao = None
            if self.color_prog:
                glDeleteProgram(self.color_prog)
                self.color_prog = None
            if self.tex_prog:
                glDeleteProgram(self.tex_prog)
                self.tex_prog = None
            for tex_id, _, _ in list(self.textures.values()):
                try:
                    glDeleteTextures([tex_id])
                except Exception:
                    pass
            self.textures.clear()
        except Exception as e:
            logging.error(f"cleanup error: {e}")

    # ---------------------- render ----------------------
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)

        # 1) pull analyzer data
        if self.analyzer is not None and self.analyzer.is_active():
            self.fft = self.analyzer.get_fft_data().astype(np.float32)
            self.audio_chunk = self.analyzer.get_audio_data().astype(np.float32)
            self.level = float(self.analyzer.get_current_level())
        else:
            # demo fallback: synth a moving multi-sine
            t = time.time()
            n = self.audio_chunk.size
            x = np.linspace(0, 1, n)
            sig = (0.3*np.sin(2*np.pi*80*x + t*0.7) +
                   0.2*np.sin(2*np.pi*330*x + t*1.1) +
                   0.1*np.sin(2*np.pi*1100*x + t*0.9))
            self.audio_chunk = sig.astype(np.float32)
            win = np.hanning(n)
            mag = np.abs(np.fft.rfft(win*sig))
            mag_db = 20*np.log10(mag+1e-10)
            self.fft = np.clip((mag_db + 60)/60*100, 0, 100).astype(np.float32)
            self.level = float(np.sqrt(np.mean(sig**2))*100)

        # 2) compute metrics
        metrics = self._compute_metrics(self.fft, self.audio_chunk, self.sample_rate)
        self._update_histories(metrics)

        # 3) update spectrogram texture
        self._update_spectrogram_row(self.fft)

        # 4) draw HUD
        self._draw_hud(metrics)

    # ---------------------- metrics ----------------------
    def _compute_metrics(self, fft_norm_0_100, audio, sr):
        eps = 1e-9
        # normalize to [0,1]
        mag = np.maximum(fft_norm_0_100.astype(np.float32) / 100.0, 0.0)
        n = mag.size
        if n <= 1:
            return {
                'centroid': 0.0,
                'spread': 0.0,
                'flatness': 0.0,
                'entropy': 0.0,
                'am_index': 0.0,
                'tonal': 0.0,
                'flux': 0.0
            }
        freqs = np.linspace(0.0, sr*0.5, n, dtype=np.float32)
        s = np.sum(mag) + eps
        centroid_hz = float(np.sum(freqs * mag) / s)
        spread_hz = float(np.sqrt(np.sum(((freqs - centroid_hz)**2) * mag) / s))
        centroid_norm = centroid_hz / (sr * 0.5)
        spread_norm = spread_hz / (sr * 0.5)

        # flatness (0=noisy?, actually high flatness=>noise). clamp 0..1
        gm = np.exp(np.mean(np.log(mag + eps)))
        am = np.mean(mag + eps)
        flatness = float(np.clip(gm / am, 0.0, 1.0))

        # spectral entropy (0..1)
        p = mag / (np.sum(mag) + eps)
        entropy = float(-np.sum(p * np.log(p + eps)) / np.log(n))

        # amplitude modulation index (rough): normalized std of absolute envelope
        env = np.abs(audio.astype(np.float32))
        if env.size > 0:
            am_index = float(np.clip(np.std(env) / (np.mean(env) + eps), 0.0, 1.0))
        else:
            am_index = 0.0

        # spectral flux (vs previous frame)
        if self.prev_fft is None or self.prev_fft.size != mag.size:
            flux = 0.0
        else:
            diff = mag - self.prev_fft
            flux = float(np.sum(np.clip(diff, 0.0, 1.0)) / n)
        self.prev_fft = mag.copy()

        # tonal vs noisy score (0=tonal,1=noisy) using flatness
        noisy_score = float(flatness)

        return {
            'centroid': float(np.clip(centroid_norm, 0.0, 1.0)),
            'spread': float(np.clip(spread_norm*2.0, 0.0, 1.0)),  # scaled a bit for visuals
            'flatness': flatness,
            'entropy': float(np.clip(entropy, 0.0, 1.0)),
            'am_index': am_index,
            'tonal': noisy_score,
            'flux': flux
        }

    def _update_histories(self, m):
        i = self.hist_pos % self.entropy_hist.size
        self.entropy_hist[i] = m['entropy']
        self.spread_hist[i] = m['spread']
        self.centroid_hist[i] = m['centroid']
        self.am_hist[i] = m['am_index']
        self.hist_pos += 1

    # ---------------------- spectrogram ----------------------
    def _init_spectrogram(self):
        # RGBA texture (we'll upload colored rows)
        self.spec_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.spec_tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        empty = (np.zeros((self.spec_h, self.spec_w, 4), dtype=np.uint8))
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.spec_w, self.spec_h, 0, GL_RGBA, GL_UNSIGNED_BYTE, empty)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.spec_row = 0

    def _update_spectrogram_row(self, fft_0_100):
        # map magnitude to RGBA using simple plasma-like palette CPU-side
        x = fft_0_100.astype(np.float32) / 100.0
        # resize to spec_w
        if x.size != self.spec_w:
            x = np.interp(np.linspace(0, 1, self.spec_w), np.linspace(0, 1, fft_0_100.size), x)
        # palette
        r = np.clip(np.sin(1.7 + x*3.1415) * 0.5 + 0.5, 0, 1)
        g = np.clip(np.sin(0.3 + x*3.5) * 0.5 + 0.5, 0, 1)
        b = np.clip(np.sin(2.3 + x*4.2) * 0.5 + 0.5, 0, 1)
        a = np.clip(0.3 + x*0.7, 0, 1)
        row = (np.stack([r, g, b, a], axis=-1) * 255).astype(np.uint8)
        glBindTexture(GL_TEXTURE_2D, self.spec_tex)
        y = self.spec_row % self.spec_h
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, y, self.spec_w, 1, GL_RGBA, GL_UNSIGNED_BYTE, row)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.spec_row += 1

    # ---------------------- drawing helpers ----------------------
    def _build_color_program(self):
        vs = """
        #version 330 core
        layout(location=0) in vec2 aPos;
        layout(location=1) in vec4 aColor;
        out vec4 vColor;
        void main(){
            gl_Position = vec4(aPos, 0.0, 1.0);
            vColor = aColor;
        }
        """
        fs = """
        #version 330 core
        in vec4 vColor; out vec4 FragColor;
        void main(){ FragColor = vColor; }
        """
        return self._link_program(vs, fs)

    def _build_tex_program(self):
        vs = """
        #version 330 core
        layout(location=0) in vec2 aPos;
        layout(location=1) in vec2 aUV;
        out vec2 vUV;
        void main(){ gl_Position = vec4(aPos, 0.0, 1.0); vUV = aUV; }
        """
        fs = """
        #version 330 core
        in vec2 vUV; out vec4 FragColor; uniform sampler2D tex0;
        void main(){ FragColor = texture(tex0, vUV); }
        """
        return self._link_program(vs, fs)

    def _link_program(self, vs_src, fs_src):
        def compile_shader(src, stype):
            sh = glCreateShader(stype)
            glShaderSource(sh, src)
            glCompileShader(sh)
            ok = glGetShaderiv(sh, GL_COMPILE_STATUS)
            if not ok:
                raise RuntimeError(glGetShaderInfoLog(sh).decode())
            return sh
        vs = compile_shader(vs_src, GL_VERTEX_SHADER)
        fs = compile_shader(fs_src, GL_FRAGMENT_SHADER)
        prog = glCreateProgram()
        glAttachShader(prog, vs)
        glAttachShader(prog, fs)
        glLinkProgram(prog)
        ok = glGetProgramiv(prog, GL_LINK_STATUS)
        glDeleteShader(vs); glDeleteShader(fs)
        if not ok:
            raise RuntimeError(glGetProgramInfoLog(prog).decode())
        return prog

    def _color(self, r,g,b,a=None):
        if a is None:
            a = self.alpha
        return (float(r), float(g), float(b), float(a))

    def _push_prims(self, verts):
        """verts: Nx6 float32 array [x,y,r,g,b,a] in NDC; draw as GL_LINES/GL_TRIANGLES outside"""
        data = np.asarray(verts, dtype=np.float32).reshape(-1, 6)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return data.shape[0]

    def _draw_lines(self, segments):
        # segments: list of (x1,y1,x2,y2, r,g,b,a)
        if not segments:
            return
        verts = []
        for (x1,y1,x2,y2, r,g,b,a) in segments:
            verts.extend([x1,y1,r,g,b,a])
            verts.extend([x2,y2,r,g,b,a])
        count = self._push_prims(verts)
        glUseProgram(self.color_prog)
        glBindVertexArray(self.vao)
        glLineWidth(self.line_width)
        glDrawArrays(GL_LINES, 0, count)
        glBindVertexArray(0)
        glUseProgram(0)

    def _draw_rect(self, x,y,w,h, color, filled=True):
        r,g,b,a = color
        if filled:
            # two triangles
            verts = [
                x,   y,   r,g,b,a,
                x+w, y,   r,g,b,a,
                x+w, y+h, r,g,b,a,
                x,   y,   r,g,b,a,
                x+w, y+h, r,g,b,a,
                x,   y+h, r,g,b,a,
            ]
            count = self._push_prims(verts)
            glUseProgram(self.color_prog)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_TRIANGLES, 0, count)
            glBindVertexArray(0)
            glUseProgram(0)
        else:
            segs = [
                (x,y, x+w,y, r,g,b,a), (x+w,y, x+w,y+h, r,g,b,a),
                (x+w,y+h, x,y+h, r,g,b,a), (x,y+h, x,y, r,g,b,a)
            ]
            self._draw_lines(segs)

    def _draw_text(self, text, x, y, w, h, align='left'):
        if not PIL_AVAILABLE:
            return
        tex = self.textures.get(text)
        if not tex:
            tex = self._build_label(text, 16)
        if not tex:
            return
        tex_id, tw, th = tex
        # compute quad in NDC
        # keep aspect by fitting height
        scale = min(w / max(1, tw), h / max(1, th))
        rw = tw * scale
        rh = th * scale
        if align == 'center':
            px = x + (w - rw) * 0.5
        elif align == 'right':
            px = x + (w - rw)
        else:
            px = x
        py = y + h - rh  # top-left origin for label box
        # build quad
        quad = np.array([
            [px,     py,      0.0, 1.0],
            [px+rw,  py,      1.0, 1.0],
            [px+rw,  py+rh,   1.0, 0.0],
            [px,     py,      0.0, 1.0],
            [px+rw,  py+rh,   1.0, 0.0],
            [px,     py+rh,   0.0, 0.0],
        ], dtype=np.float32)
        # upload temp VBO for tex shader
        glUseProgram(self.tex_prog)
        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, quad.nbytes, quad, GL_STREAM_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindTexture(GL_TEXTURE_2D, 0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        glDeleteBuffers(1, [vbo])
        glDeleteVertexArrays(1, [vao])
        glUseProgram(0)

    def _build_label(self, text, size=16):
        if not PIL_AVAILABLE:
            return None
        try:
            font = None
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", size)
            except Exception:
                font = ImageFont.load_default()
            # render text
            pad = 4
            img = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            tw, th = draw.textlength(text, font=font), font.size + 2
            W, H = int(tw + pad*2), int(th + pad*2)
            img = Image.new("RGBA", (max(2, W), max(2, H)), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            # text color slightly translucent for HUD feel
            draw.text((pad, pad), text, fill=(230, 240, 255, 220), font=font)
            # upload to GL
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            data = np.array(img, dtype=np.uint8)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
            glBindTexture(GL_TEXTURE_2D, 0)
            self.textures[text] = (tex_id, img.width, img.height)
            return self.textures[text]
        except Exception as e:
            logging.error(f"label build failed for '{text}': {e}")
            return None

    # ---------------------- HUD composition ----------------------
    def _draw_hud(self, m):
        # Colors
        fg = self._color(0.85, 0.95, 1.0, 0.95)
        grid = self._color(0.25, 0.35, 0.5, 0.6)
        accent = self._color(0.2, 0.7, 1.0, 0.9)
        warn = self._color(1.0, 0.3, 0.2, 0.9)
        okc = self._color(0.2, 0.9, 0.4, 0.9)

        # Panels (NDC): define rects
        # left big scatter
        axA = (-0.95, 0.2, 0.75, 0.7)
        # right spectrogram
        axB = ( -0.15, 0.2, 1.05, 0.7)
        # bottom left bars
        axC = (-0.95, -0.6, 0.95, 0.35)
        # bottom right AM plot
        axD = (-0.95, -0.95, 1.85, 0.3)

        # frames
        self._draw_rect(*axA, grid, filled=False)
        self._draw_rect(*axB, grid, filled=False)
        self._draw_rect(*axC, grid, filled=False)
        self._draw_rect(*axD, grid, filled=False)

        # Titles
        self._draw_text("SPREAD–ENTROPY SPACE", axA[0]+0.02, axA[1]+axA[3]-0.08, 0.5, 0.07, 'left')
        self._draw_text("SPECTROGRAM", axB[0]+0.02, axB[1]+axB[3]-0.08, 0.5, 0.07, 'left')
        self._draw_text("SPECTRAL SPREAD", axC[0]+0.02, axC[1]+axC[3]-0.08, 0.45, 0.06, 'left')
        self._draw_text("SPECTRAL FLATNESS", axC[0]+0.5, axC[1]+axC[3]-0.08, 0.45, 0.06, 'left')
        self._draw_text("SPECTRAL CENTROID", axC[0]+0.02, axC[1]+0.10, 0.45, 0.06, 'left')
        self._draw_text("AMPLITUDE MODULATION", axD[0]+0.02, axD[1]+axD[3]-0.08, 0.6, 0.06, 'left')

        # Grid lines for panel A
        segs = []
        gx, gy, gw, gh = axA
        for i in range(1, 5):
            t = i/5.0
            segs.append((gx + gw*t, gy, gx + gw*t, gy+gh, *grid))
            segs.append((gx, gy + gh*t, gx+gw, gy + gh*t, *grid))
        self._draw_lines(segs)

        # Scatter point (spread=x, entropy=y)
        px = gx + gw * float(np.clip(m['spread'], 0.0, 1.0))
        py = gy + gh * float(np.clip(m['entropy'], 0.0, 1.0))
        self._draw_rect(px-0.008, py-0.008, 0.016, 0.016, accent, filled=True)

        # Spectrogram quad (axB). Map texture with vertical wrap-by-row trick
        self._draw_spectrogram(axB)

        # Bars (spread, flatness, centroid)
        # Spread bar (left area of C)
        bx, by, bw, bh = axC
        barw = (bw*0.45) - 0.04
        self._bar(bx+0.02, by+0.02, barw, 0.06, m['spread'], accent, grid)
        # Flatness bar (right area of C)
        self._bar(bx+0.50, by+0.02, barw, 0.06, m['flatness'], okc, grid)
        # Centroid marker across mini axis
        # draw baseline axis
        segs = [(bx+0.02, by+0.10, bx+0.02+barw, by+0.10, *grid)]
        self._draw_lines(segs)
        cx = (bx+0.02) + barw * float(np.clip(m['centroid'], 0.0, 1.0))
        self._draw_rect(cx-0.005, by+0.085, 0.01, 0.03, self._color(1,1,0,0.9), True)

        # AM modulation trace (history)
        dx, dy, dw, dh = axD
        # grid
        segs = []
        for i in range(1, 8):
            t = i/8.0
            segs.append((dx + dw*t, dy, dx + dw*t, dy+dh, *grid))
        for i in range(1, 3):
            t = i/3.0
            segs.append((dx, dy + dh*t, dx+dw, dy + dh*t, *grid))
        self._draw_lines(segs)
        # polyline from history
        hist = self._cyclical(self.am_hist)
        pts = []
        for i, v in enumerate(hist):
            x = dx + dw * (i / max(1, hist.size-1))
            y = dy + dh * float(np.clip(v, 0.0, 1.0))
            pts.append((x, y))
        self._polyline(pts, accent)

        # Tonal / Noisy indicator in footer right
        score = float(np.clip(m['tonal'], 0.0, 1.0))
        tbarx = axD[0]+axD[2]-0.35
        tbary = axD[1]+0.02
        self._draw_text("TONAL", tbarx-0.02, tbary+0.065, 0.08, 0.05, 'right')
        self._draw_text("NOISY", tbarx+0.28, tbary+0.065, 0.08, 0.05, 'right')
        self._bar(tbarx, tbary, 0.30, 0.03, score, warn, grid)

    def _bar(self, x,y,w,h, value01, col, gridcol):
        self._draw_rect(x, y, w, h, self._color(0.1,0.2,0.3,0.35), True)
        self._draw_rect(x, y, w, h, gridcol, False)
        self._draw_rect(x, y, max(0.0, min(w*value01, w)), h, col, True)

    def _polyline(self, pts, color):
        if len(pts) < 2:
            return
        segs = []
        r,g,b,a = color
        for i in range(len(pts)-1):
            x1,y1 = pts[i]
            x2,y2 = pts[i+1]
            segs.append((x1,y1,x2,y2,r,g,b,a))
        self._draw_lines(segs)

    def _draw_spectrogram(self, rect):
        x,y,w,h = rect
        # draw background
        self._draw_rect(x, y, w, h, self._color(0.05,0.08,0.12,0.5), True)
        # draw texture as two quads to simulate vertical scrolling wrap
        if not self.spec_tex:
            return
        glUseProgram(self.tex_prog)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.spec_tex)
        # We draw the texture in two parts: [row..end] and [0..row]
        part1_h = (self.spec_h - (self.spec_row % self.spec_h)) / self.spec_h
        # part1 quad
        self._draw_tex_quad(x, y + h*(1.0-part1_h), w, h*part1_h,
                             0.0, (self.spec_row % self.spec_h)/self.spec_h,
                             1.0, 1.0)
        # part2 quad
        self._draw_tex_quad(x, y, w, h*(1.0-part1_h),
                             0.0, 0.0,
                             1.0, (self.spec_row % self.spec_h)/self.spec_h)
        glBindTexture(GL_TEXTURE_2D, 0)
        glUseProgram(0)

    def _draw_tex_quad(self, x,y,w,h, u0,v0,u1,v1):
        quad = np.array([
            [x,   y,    u0, v0],
            [x+w, y,    u1, v0],
            [x+w, y+h,  u1, v1],
            [x,   y,    u0, v0],
            [x+w, y+h,  u1, v1],
            [x,   y+h,  u0, v1],
        ], dtype=np.float32)
        vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)
        glBindVertexArray(vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, quad.nbytes, quad, GL_STREAM_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        glDeleteBuffers(1, [vbo])
        glDeleteVertexArrays(1, [vao])

    def _cyclical(self, arr):
        # return history ordered oldest->newest based on hist_pos
        i = self.hist_pos % arr.size
        if i == 0:
            return arr.copy()
        return np.concatenate([arr[i:], arr[:i]])

    # ---------------------- UI controls ----------------------
    def get_controls(self):
        return {
            "FFT Smoothing": {"type": "slider", "min": 0, "max": 100, "value": int(self.fft_smooth*100)},
            "Line Width": {"type": "slider", "min": 1, "max": 4, "value": int(self.line_width)},
            "Alpha": {"type": "slider", "min": 20, "max": 100, "value": int(self.alpha*100)},
        }

    def update_control(self, name, value):
        if name == "FFT Smoothing":
            self.fft_smooth = float(value)/100.0
            if self.analyzer:
                self.analyzer.set_smoothing(fft_smooth=self.fft_smooth)
        elif name == "Line Width":
            self.line_width = float(value)
        elif name == "Alpha":
            self.alpha = float(value)/100.0

