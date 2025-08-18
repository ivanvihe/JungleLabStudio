import sys
import logging
logging.basicConfig(level=logging.DEBUG)

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QSurfaceFormat

from visuals.presets.fluid_particles import FluidParticlesVisualizer

if __name__ == "__main__":
    logging.debug("Application starting")
    format = QSurfaceFormat()
    format.setVersion(3, 3)
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    format.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(format)
    logging.debug("QSurfaceFormat set")

    app = QApplication(sys.argv)
    logging.debug("QApplication created")

    window = QMainWindow()
    window.setWindowTitle("Fluid Particles Debug")
    window.setGeometry(100, 100, 800, 600)

    visualizer = FluidParticlesVisualizer()
    window.setCentralWidget(visualizer)
    logging.debug("FluidParticlesVisualizer created and set as central widget")

    window.show()
    logging.debug("Window shown")

    logging.debug("Starting app.exec()")
    exit_code = app.exec()
    logging.debug(f"app.exec() finished with exit code: {exit_code}")
    sys.exit(exit_code)
