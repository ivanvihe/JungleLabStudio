export class MidiEngine {
    constructor() {
        this.inputs = [];
        this.callbacks = new Map();
    }

    async init() {
        if (!navigator.requestMIDIAccess) {
            console.warn('Web MIDI API not supported');
            return;
        }
        const access = await navigator.requestMIDIAccess();
        access.inputs.forEach(input => {
            input.onmidimessage = this._onMIDIMessage.bind(this);
            this.inputs.push(input);
        });
    }

    on(type, fn) {
        this.callbacks.set(type, fn);
    }

    _onMIDIMessage(message) {
        const [status, data1, data2] = message.data;
        const type = status & 0xf0;
        const cb = this.callbacks.get(type);
        if (cb) cb({ status, data1, data2 });
    }
}
