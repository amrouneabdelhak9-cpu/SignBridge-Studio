# ui/main_window.py
"""
SignBridge Studio — Main Window
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QLabel, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor

from components.sidebar import Sidebar
from ui.splash_screen import SplashScreen
from ui.dashboard_screen import DashboardScreen
from ui.translation_screen import TranslationScreen
from ui.learning_screen import LearningScreen
from ui.quiz_screen import QuizScreen
from ui.training_screen import TrainingScreen
from ui.pipeline_test_screen import PipelineTestScreen
from backend.sign_bridge_engine import SignBridgeBackend
from controllers.training_controller import TrainingController

BG = "#02040B"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SignBridge Studio")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 800)

        central = QWidget()
        central.setStyleSheet(f"background: {BG};")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.navigation_changed.connect(self._on_sidebar_nav)
        self._sidebar.hide()
        main_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")
        main_layout.addWidget(self._stack, 1)

        self._init_backend()
        self._setup_screens()
        self._init_training_controller()

        self._stack.setCurrentIndex(0)
        self._current_page = "splash"

    def _init_backend(self):
        model_dir = "model"
        api_key = ""
        self._backend = SignBridgeBackend(
            model_dir=model_dir,
            groq_api_key=api_key,
            device="cpu",
            parent=self
        )

    def _init_training_controller(self):
        self._training_controller = TrainingController(
            model_dir    = "models",
            dataset_root = ".",
            camera_index = 0,
            device       = "cpu",
            epochs       = 30,
            face_features= False,
            min_samples  = 1,
            parent       = self,
        )

        self._training_controller.attach(self._training)
        self._training.camera_stop_requested.connect(
            self._training_controller.stop_camera
        )
        self._training_controller.training_complete.connect(
            self._on_training_complete
        )
        self._training_controller.status_message.connect(
            lambda msg: print(f"[Training] {msg}")
        )

    def _on_training_complete(self, accuracy: str):
        print(f"[Training] Complete — accuracy: {accuracy}")

    def _setup_screens(self):
        self._splash = SplashScreen()
        self._splash.enter_clicked.connect(self._show_dashboard)

        self._dashboard = DashboardScreen()
        self._dashboard.navigate_to.connect(self._navigate_to)

        self._translation = TranslationScreen()
        self._translation.set_backend(self._backend)

        self._learning = LearningScreen()
        self._learning.sign_selected.connect(lambda s: print(f"Sign: {s}"))

        self._quiz = QuizScreen()
        self._training = TrainingScreen()
        self._pipeline_test = PipelineTestScreen()
        self._pipeline_test.navigate_to.connect(self._navigate_to)

        self._stack.addWidget(self._splash)         # 0
        self._stack.addWidget(self._dashboard)        # 1
        self._stack.addWidget(self._translation)    # 2
        self._stack.addWidget(self._learning)       # 3
        self._stack.addWidget(self._quiz)           # 4
        self._stack.addWidget(self._training)       # 5
        self._stack.addWidget(self._pipeline_test)  # 6

    def _show_dashboard(self):
        self._switch_page("home", 1)
        self._sidebar.show()
        self._sidebar.set_active("home")

    def _on_sidebar_nav(self, nav_id: str):
        screen_map = {
            "home":        1,
            "translation": 2,
            "learn":       3,
            "quiz":        4,
            "training":    5,
            "diagnostics": 6,
        }
        idx = screen_map.get(nav_id, 1)
        self._switch_page(nav_id, idx)
        self._sidebar.set_active(nav_id)

    def _navigate_to(self, screen: str):
        screen_map = {
            "home":        1,
            "translation": 2,
            "learn":       3,
            "quiz":        4,
            "training":    5,
            "diagnostics": 6,
        }
        idx = screen_map.get(screen, 1)
        self._switch_page(screen, idx)
        self._sidebar.set_active(screen)

    def _switch_page(self, page_name: str, index: int) -> None:
        print(f"[MainWindow] Switching from '{self._current_page}' to '{page_name}'")

        if self._current_page == page_name:
            self._stack.setCurrentIndex(index)
            return

        needs_camera_release = False

        if self._current_page == "training" and page_name != "training":
            if hasattr(self, "_training_controller"):
                print("[MainWindow] Stopping training camera...")
                self._training_controller.stop_camera()
                needs_camera_release = True

        if self._current_page == "translation" and page_name != "translation":
            if hasattr(self, "_backend"):
                print("[MainWindow] Stopping translation backend...")
                self._backend.stop_session()
                needs_camera_release = True

        self._current_page = page_name

        if needs_camera_release:
            # ← 2.5 seconds — enough for Windows DirectShow to fully release
            QTimer.singleShot(2500, lambda: self._do_switch(index, page_name))
        else:
            self._do_switch(index, page_name)

    def _do_switch(self, index: int, page_name: str) -> None:
        print(f"[MainWindow] _do_switch to '{page_name}'")
        self._stack.setCurrentIndex(index)

        if page_name == "translation":
            # Wait extra 500ms after page switch before starting camera
            QTimer.singleShot(500, self._start_translation_session)

    def _start_translation_session(self) -> None:
        print("[MainWindow] _start_translation_session called")
        if hasattr(self, "_backend") and self._backend:
            running = self._backend.is_running()
            print(f"[MainWindow] Backend is_running: {running}")
            if not running:
                print("[MainWindow] Starting translation session...")
                self._backend.start_session()
            else:
                print("[MainWindow] Backend already running, not starting")
        else:
            print("[MainWindow] ⚠️ No backend available!")

    def closeEvent(self, event):
        print("[MainWindow] closeEvent — shutting down...")
        if hasattr(self, "_backend") and self._backend:
            self._backend.stop_session()

        if hasattr(self, "_training_controller"):
            self._training_controller.shutdown()

        event.accept()