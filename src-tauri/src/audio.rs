use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use rustfft::{FftPlanner, num_complex::Complex};
use tauri::AppHandle;

pub fn start(app: AppHandle) {
    tauri::async_runtime::spawn(async move {
        if let Err(e) = run(app.clone()) {
            eprintln!("audio error: {e:?}");
        }
    });
}

fn run(app: AppHandle) -> anyhow::Result<()> {
    let host = cpal::default_host();
    let device = host.default_input_device().ok_or_else(|| anyhow::anyhow!("no input device"))?;
    let config = device.default_input_config()?;
    let fft_size = 1024usize;
    let mut planner = FftPlanner::<f32>::new();
    let fft = planner.plan_fft_forward(fft_size);
    let mut buffer: Vec<Complex<f32>> = vec![Complex{ re:0.0, im:0.0}; fft_size];

    let stream = device.build_input_stream(
        &config.into(),
        move |data: &[f32], _| {
            for (i, sample) in data.iter().enumerate().take(fft_size) {
                buffer[i].re = *sample;
                buffer[i].im = 0.0;
            }
            fft.process(&mut buffer);
            let mags: Vec<f32> = buffer.iter().map(|c| c.norm()).collect();
            let _ = app.emit_all("fft", mags);
        },
        move |err| eprintln!("stream error: {err}")
    )?;
    stream.play()?;
    std::thread::park();
    Ok(())
}
