mod gpu;
mod midi;
mod audio;
mod config;

use config::{Config, ConfigState, LayerConfig};
use tauri::{Manager, State};

#[tauri::command]
async fn set_layer_opacity(layer: String, opacity: f32, state: State<'_, ConfigState>) {
    let mut cfg = state.inner.lock().unwrap();
    if let Some(l) = cfg.layers.get_mut(&layer) {
        l.opacity = opacity;
    } else {
        cfg.layers.insert(layer.clone(), LayerConfig { opacity, ..Default::default() });
    }
}

#[tauri::command]
async fn get_config(state: State<'_, ConfigState>) -> Config {
    let cfg = state.inner.lock().unwrap();
    cfg.clone()
}

#[tauri::command]
async fn save_config(state: State<'_, ConfigState>) -> Result<(), String> {
    let cfg = state.inner.lock().unwrap();
    cfg.save(&state.path).map_err(|e| e.to_string())
}

fn main() {
    let config_path = tauri::api::path::app_config_dir(&tauri::Config::default())
        .unwrap_or(std::path::PathBuf::from("."))
        .join("config.json");
    let cfg = Config::load(&config_path);

    tauri::Builder::default()
        .manage(ConfigState { path: config_path, inner: std::sync::Mutex::new(cfg) })
        .manage(midi::MidiState::default())
        .invoke_handler(tauri::generate_handler![
            set_layer_opacity,
            get_config,
            save_config,
            midi::list_midi_ports,
            midi::select_midi_port
        ])
        .setup(|app| {
            midi::start(app.handle().clone());
            audio::start(app.handle().clone());
            tauri::async_runtime::spawn(gpu::init());
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error running tauri application");
}
