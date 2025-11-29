from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHADER_DIR = ROOT / "shaders"


def shader_path(name: str) -> Path:
    return SHADER_DIR / name


def load_shader(name: str) -> str:
    return shader_path(name).read_text()
