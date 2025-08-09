import { Pane } from 'tweakpane';

const pane = new Pane({ container: document.getElementById('controls') });
const params = { sensitivity: 0.5 };

pane.addBinding(params, 'sensitivity', { min: 0, max: 1 }).on('change', (ev) => {
    window.electronAPI.send('control-change', { param: 'sensitivity', value: ev.value });
});
