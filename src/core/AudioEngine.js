export class AudioEngine {
    constructor() {
        this.audioCtx = null;
        this.analyser = null;
        this.freqData = null;
    }

    async init() {
        if (!navigator.mediaDevices) {
            console.warn('Media devices not available');
            return;
        }
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const source = this.audioCtx.createMediaStreamSource(stream);
        this.analyser = this.audioCtx.createAnalyser();
        this.analyser.fftSize = 2048;
        source.connect(this.analyser);
        this.freqData = new Uint8Array(this.analyser.frequencyBinCount);
    }

    update() {
        if (!this.analyser) return;
        this.analyser.getByteFrequencyData(this.freqData);
    }

    getFrequencies() {
        return this.freqData;
    }
}
