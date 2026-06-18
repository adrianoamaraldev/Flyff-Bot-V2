use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::Manager;

#[cfg(windows)]
use std::os::windows::process::CommandExt;
#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

static PYTHON_PROCESS: Mutex<Option<Child>> = Mutex::new(None);

fn spawn_backend(app: &tauri::AppHandle) {
    let child = if cfg!(debug_assertions) {
        spawn_dev()
    } else {
        spawn_release(app)
    };

    match child {
        Ok(c) => { *PYTHON_PROCESS.lock().unwrap() = Some(c); }
        Err(e) => { eprintln!("Falha ao iniciar backend: {}", e); }
    }
}

/// Dev: Python do venv + api.py
fn spawn_dev() -> std::io::Result<Child> {
    let exe_path = std::env::current_exe().expect("current_exe falhou");
    let project_root = exe_path
        .parent().unwrap()
        .parent().unwrap()
        .parent().unwrap()
        .parent().unwrap()
        .parent().unwrap()
        .to_path_buf();

    let python = if cfg!(windows) {
        project_root.join("venv").join("Scripts").join("python.exe")
    } else {
        project_root.join("venv").join("bin").join("python")
    };

    let backend_dir = project_root.join("backend");
    let script = backend_dir.join("api.py");

    println!("Backend (dev): {:?}", script);
    Command::new(&python).arg(&script).current_dir(&backend_dir).spawn()
}

/// Release: backend.exe bundled no resource dir
fn spawn_release(app: &tauri::AppHandle) -> std::io::Result<Child> {
    let resource_dir = app.path().resource_dir()
        .expect("Falha ao obter resource_dir");

    let backend_dir = resource_dir.join("backend");
    let backend_exe = backend_dir.join("backend.exe");

    println!("Backend (release): {:?}", backend_exe);
    #[cfg(windows)]
    return Command::new(&backend_exe)
        .current_dir(&backend_dir)
        .creation_flags(CREATE_NO_WINDOW)
        .spawn();

    #[cfg(not(windows))]
    Command::new(&backend_exe).current_dir(&backend_dir).spawn()
}

fn kill_backend() {
    if let Some(mut child) = PYTHON_PROCESS.lock().unwrap().take() {
        let _ = child.kill();
        println!("Backend encerrado.");
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            spawn_backend(app.handle());
            Ok(())
        })
        .on_window_event(|_window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                kill_backend();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
