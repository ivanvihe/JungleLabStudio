use log::error;
use midir::{Ignore, MidiInput};
use tauri::AppHandle;

pub fn start(app: AppHandle) -> anyhow::Result<()> {
    tauri::async_runtime::spawn(async move {
        if let Err(e) = run(app.clone()).await {
            error!("midi error: {e:?}");
            let _ = app.emit_all("error", format!("midi error: {e}"));
        }
    });
    Ok(())
}

async fn run(app: AppHandle) -> anyhow::Result<()> {
    let mut midi_in = MidiInput::new("tauri-midi")?;
    midi_in.ignore(Ignore::None);
    let ports = midi_in.ports();
    let in_port = ports
        .get(0)
        .ok_or_else(|| anyhow::anyhow!("no midi input"))?;
    let app_clone = app.clone();
    let _conn = midi_in.connect(
        in_port,
        "midir",
        move |_stamp, message, _| {
            if message.len() >= 3 {
                let status = message[0];
                let channel = status & 0x0F; // 0-indexed
                if (13..=15).contains(&channel) {
                    let note = message[1];
                    let vel = message[2];
                    let _ = app_clone.emit_all("midi", &(channel + 1, note, vel));
                }
            }
        },
        (),
    )?;

    futures::future::pending::<()>().await;
    Ok(())
}
