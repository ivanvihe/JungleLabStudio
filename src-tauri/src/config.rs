use serde::{Deserialize, Serialize};
use std::{collections::HashMap, fs, path::PathBuf, sync::Mutex};

#[derive(Serialize, Deserialize, Clone)]
pub struct LayerConfig {
    pub opacity: f32,
    pub fade_ms: u64,
    pub thumbnail: String,
    pub midi_channel: u8,
}

impl Default for LayerConfig {
    fn default() -> Self {
        Self { opacity: 1.0, fade_ms: 200, thumbnail: String::new(), midi_channel: 0 }
    }
}

#[derive(Serialize, Deserialize, Clone)]
pub struct Config {
    pub layers: HashMap<String, LayerConfig>,
}

impl Default for Config {
    fn default() -> Self {
        let mut layers = HashMap::new();
        layers.insert("A".into(), LayerConfig { midi_channel: 14, ..Default::default() });
        layers.insert("B".into(), LayerConfig { midi_channel: 15, ..Default::default() });
        layers.insert("C".into(), LayerConfig { midi_channel: 16, ..Default::default() });
        Self { layers }
    }
}

impl Config {
    pub fn load(path: &PathBuf) -> Self {
        if let Ok(text) = fs::read_to_string(path) {
            if let Ok(cfg) = serde_json::from_str(&text) {
                return cfg;
            }
        }
        Self::default()
    }

    pub fn save(&self, path: &PathBuf) -> anyhow::Result<()> {
        let text = serde_json::to_string_pretty(self)?;
        fs::write(path, text)?;
        Ok(())
    }
}

pub struct ConfigState {
    pub path: PathBuf,
    pub inner: Mutex<Config>,
}
