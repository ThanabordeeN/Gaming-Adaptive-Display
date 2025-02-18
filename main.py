import sys
import os
import json
import psutil
import winreg  # For Windows registry operations
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QListWidget, QGroupBox, QTextEdit, QMenu, QSystemTrayIcon, QCheckBox
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer, Qt
from resolution_utils import DEVMODEW, change_resolution_refresh, reset_resolution_refresh, get_current_resolution_refresh

def get_game_name(game_path):
    return os.path.basename(game_path)

class GameResolutionChanger(QWidget):
    def __init__(self):
        super().__init__()
        self.list_of_game = []
        self.list_of_applied_games = []
        self.resolution_changed = False
        try:
            if os.path.exists("./game_config.json"):
                with open("./game_config.json", "r") as f:
                    config = json.load(f)
                    self.list_of_applied_games = config.get("games", [])
                    self.list_of_game = [get_game_name(game["game"]) for game in self.list_of_applied_games]
        except json.JSONDecodeError:
            print("Error reading config file, starting with empty lists")
        self.initUI()
        self.init_tray()
        self.watch_dog()

    def initUI(self):
        self.setWindowTitle("Gaming Adaptive Display")
        self.setWindowIcon(QIcon("icon.png"))  # Set the window's icon

        self.setGeometry(100, 100, 450, 450)
        self.setStyleSheet("""
            QWidget {
                font-family: Arial;
                font-size: 14px;
            }
            QGroupBox {
                font-weight: bold;
                margin-top: 10px;
            }
            QPushButton {
                padding: 6px;
            }
        """)

        main_layout = QVBoxLayout()

        # Game selection group
        game_group = QGroupBox("Game Selection")
        game_layout = QVBoxLayout()

        self.game_combo = QTextEdit()
        self.game_combo.setFixedHeight(30)
        self.game_combo.setToolTip("Type or select a game executable path")
        self.browse_button = QPushButton("Browse")
        self.browse_button.setToolTip("Browse for a game executable")
        self.browse_button.clicked.connect(self.browse_game)
        game_select_layout = QHBoxLayout()
        game_select_layout.addWidget(self.game_combo)
        game_select_layout.addWidget(self.browse_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.setToolTip("Remove selected game from monitored list")
        self.remove_button.clicked.connect(self.remove_game)
  
        self.listed_games = QListWidget()
        self.listed_games.setToolTip("List of monitored games")
        for game in self.list_of_game:
            self.listed_games.addItem(f"{game} ({next((g['resolution'] for g in self.list_of_applied_games if get_game_name(g['game']) == game), 'No resolution set')})")

        game_layout.addWidget(QLabel("Select or enter game path:"))
        game_layout.addLayout(game_select_layout)
        game_layout.addWidget(QLabel("Monitored Games:"))
        game_layout.addWidget(self.listed_games)
        game_layout.addWidget(self.remove_button)
        game_group.setLayout(game_layout)

        # Resolution selection group
        res_group = QGroupBox("Resolution Settings")
        res_layout = QVBoxLayout()

        self.resolution_combo = QComboBox()
        self.resolution_combo.setToolTip("Select desired resolution and refresh rate")
        
        # Get current resolution and refresh rate
        current_width, current_height, current_refresh = get_current_resolution_refresh()
        
        # Common resolutions
        resolutions = [
            "3840x2160", # 4K
            "3440x1440", # Ultrawide 1440p
            "2560x1440", # 1440p
            "1920x1080", # 1080p
            "1680x1050", # WSXGA+
            "1600x900",  # HD+
            "1440x900",  # WXGA+
            "1366x768",  # HD
            "1280x1024", # SXGA
            "1280x800",  # WXGA
            "1280x720",  # 720p
            "1024x768",  # XGA
            "800x600",   # SVGA
            "640x480"    # VGA
        ]
        
        # Common refresh rates
        refresh_rates = ["60", "75", "120", "144", "165", "240"]
        self.refresh_rates_combo = QComboBox()
        self.refresh_rates_combo.addItems(refresh_rates)

        
        # Generate all combinations
        self.resolution_combo.addItems(resolutions)
        
        # Set current resolution as default
        current_resolution = f"{current_width}x{current_height} @ {current_refresh}Hz"
        index = self.resolution_combo.findText(current_resolution)
        if index >= 0:
            self.resolution_combo.setCurrentIndex(index)
        
        res_layout.addWidget(QLabel("Select Resolution:"))
        res_layout.addWidget(self.resolution_combo)
        res_layout.addWidget(QLabel("Select refresh rate:"))
        res_layout.addWidget(self.refresh_rates_combo)
        res_group.setLayout(res_layout)

        # Run at startup checkbox
        self.startup_checkbox = QCheckBox("Run at Startup")
        self.startup_checkbox.setToolTip("Automatically start the app when Windows starts")
        self.startup_checkbox.setChecked(self.is_run_at_startup_enabled())
        self.startup_checkbox.stateChanged.connect(self.toggle_run_at_startup)

        # Apply & status section
        self.apply_button = QPushButton("Apply")
        self.apply_button.setToolTip("Apply the selected resolution for the chosen game")
        self.apply_button.clicked.connect(self.apply_resolution)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: green;")

        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setToolTip("Logs and messages")
        self.status_log.setFixedHeight(100)

        main_layout.addWidget(game_group)
        main_layout.addWidget(res_group)
        main_layout.addWidget(self.startup_checkbox)
        main_layout.addWidget(self.apply_button)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.status_log)
        self.setLayout(main_layout)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        self.tray_icon.setVisible(True)

        tray_menu = QMenu()
        restore_action = QAction("Restore", self)
        restore_action.triggered.connect(self.show_normal)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(restore_action)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)

    def show_normal(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Application Minimized",
            "The app is still running in the background. Double-click the tray icon to restore.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def browse_game(self):
        game_path, _ = QFileDialog.getOpenFileName(self, "Select Game", "", "Executable Files (*.exe)")
        if game_path:
            self.game_combo.setText(game_path)
            game_name = get_game_name(game_path)
            if game_name not in self.list_of_game:
                self.list_of_game.append(game_name)
                self.list_of_applied_games.append({
                    "game": game_path,
                    "resolution": "1920x1080 @ 165Hz"
                })
                self.listed_games.addItem(game_name)
            self.status_label.setText(f"Selected game: {game_name}")
            self.status_log.append(f"Game {game_name} added to list.")

    def apply_resolution(self):
        selected_items = self.listed_games.selectedItems()
        if not selected_items:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("No game selected!")
            return
        
        current_game = selected_items[0].text().split(" (")[0]
        current_row = self.listed_games.row(selected_items[0])
        self.listed_games.takeItem(current_row)
        self.listed_games.insertItem(current_row, f"{current_game} ({self.resolution_combo.currentText()} @ {self.refresh_rates_combo.currentText()}Hz)")

        current_game_path = next((game_path["game"] for game_path in self.list_of_applied_games if get_game_name(game_path["game"]) == current_game), None)        
        if not current_game_path:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("Error: Game path cannot be empty!")
            return

        resolution = f"{self.resolution_combo.currentText()} @ {self.refresh_rates_combo.currentText()}Hz"
        game_exists = False
        game_index = -1

        for index, game_config in enumerate(self.list_of_applied_games):
            if game_config["game"] == current_game_path:
                game_exists = True
                game_index = index
                break

        if game_exists:
            if self.list_of_applied_games[game_index]["resolution"] == resolution:
                self.status_label.setStyleSheet("color: red;")
                self.status_label.setText("Error: Resolution already applied for this game!")
                return
            self.list_of_applied_games[game_index]["resolution"] = resolution
            status_message = f"Updated resolution to {resolution} for {current_game_path}"
            log_message = f"Updated {current_game_path} with resolution {resolution}."
        else:
            self.list_of_applied_games.append({
                "game": current_game_path,
                "resolution": resolution
            })
            status_message = f"Applied {resolution} for {current_game_path}"
            log_message = f"Configured {current_game_path} with resolution {resolution}."
            game_name = get_game_name(current_game_path)
            if game_name not in self.list_of_game:
                self.list_of_game.append(game_name)
                self.listed_games.addItem(game_name)

        with open("./game_config.json", "w") as f:
            json.dump({"games": self.list_of_applied_games}, f)
        self.status_label.setStyleSheet("color: green;")
        self.status_label.setText(status_message)
        self.status_log.append(log_message)

    def remove_game(self):
        selected_items = self.listed_games.selectedItems()
        if not selected_items:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("No game selected to remove.")
            return

        for item in selected_items:
            game_name = item.text()
            row = self.listed_games.row(item)
            self.listed_games.takeItem(row)
            if game_name in self.list_of_game:
                self.list_of_game.remove(game_name)
            self.list_of_applied_games = [g for g in self.list_of_applied_games if get_game_name(g["game"]) != game_name]
            self.status_log.append(f"Removed {game_name} from the monitored list.")

        with open("./game_config.json", "w") as f:
            json.dump({"games": self.list_of_applied_games}, f)
        self.status_label.setStyleSheet("color: green;")
        self.status_label.setText("Selected game(s) removed.")

    def watch_dog(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.monitor)
        self.timer.setInterval(1000)
        self.timer.start()

    def monitor(self):
        game_running = False
        for game in self.list_of_applied_games:
            game_name = get_game_name(game["game"])
            for process in psutil.process_iter(['name']):
                try:
                    if process.info['name'].lower() == game_name.lower():
                        res = game["resolution"].split(" @ ")
                        width, height = map(int, res[0].split("x"))
                        refresh_rate = int(res[1].replace("Hz", ""))
                        if not self.resolution_changed:
                            self.resolution_changed = change_resolution_refresh(width, height, refresh_rate)
                            if self.resolution_changed:
                                self.status_log.append(f"Resolution changed to {width}x{height} @ {refresh_rate}Hz for {game_name}")
                        game_running = True
                        break

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        if not game_running and self.resolution_changed:
            if reset_resolution_refresh():
                self.status_log.append("Reset to default resolution as no monitored game is running.")
            self.resolution_changed = False

    def toggle_run_at_startup(self, state):
        enabled = state == Qt.CheckState.Checked.value
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            app_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
            if enabled:
                winreg.SetValueEx(key, "GamingAdaptiveDisplay", 0, winreg.REG_SZ, app_path)
                self.status_log.append("Enabled run at startup.")
            else:
                try:
                    winreg.DeleteValue(key, "GamingAdaptiveDisplay")
                    self.status_log.append("Disabled run at startup.")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            self.status_log.append(f"Error updating startup setting: {e}")

    def is_run_at_startup_enabled(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "GamingAdaptiveDisplay")
            winreg.CloseKey(key)
            return os.path.abspath(__file__) in value
        except Exception:
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameResolutionChanger()
    window.show()
    sys.exit(app.exec())