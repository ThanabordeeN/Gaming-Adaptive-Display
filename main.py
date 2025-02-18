import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QComboBox, QPushButton, QVBoxLayout,
    QHBoxLayout, QFileDialog, QListWidget, QGroupBox, QTextEdit
)
from PyQt6.QtCore import QTimer, Qt
import psutil
import os
import json
# Import the new module
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
        self.watch_dog()

    def initUI(self):
        self.setWindowTitle("Gaming Adaptive Display")
        self.setGeometry(100, 100, 450, 400)
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

        # --- Added Remove Button ---
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
        # --- Added Remove Button into layout ---
        game_layout.addWidget(self.remove_button)
        # -----------------------------------------
        game_group.setLayout(game_layout)

        # Resolution selection group
        res_group = QGroupBox("Resolution Settings")
        res_layout = QVBoxLayout()

        self.resolution_combo = QComboBox()
        self.resolution_combo.setToolTip("Select desired resolution and refresh rate")
        self.resolution_combo.addItems([
            "3840x2160 @ 165Hz", # 4K
            "3440x1440 @ 165Hz", # Ultrawide 1440p
            "2560x1440 @ 165Hz", # 1440p
            "1920x1080 @ 165Hz", # 1080p
            "1680x1050 @ 165Hz", # WSXGA+
            "1600x900 @ 165Hz",  # HD+
            "1440x900 @ 165Hz",  # WXGA+
            "1366x768 @ 165Hz",  # HD
            "1280x1024 @ 165Hz", # SXGA
            "1280x800 @ 165Hz",  # WXGA
            "1280x720 @ 165Hz",  # 720p
            "1024x768 @ 165Hz",  # XGA
            "800x600 @ 165Hz",   # SVGA
            "640x480 @ 165Hz"    # VGA
        ])

        res_layout.addWidget(QLabel("Select Resolution:"))
        res_layout.addWidget(self.resolution_combo)
        res_group.setLayout(res_layout)

        # Apply & status section
        self.apply_button = QPushButton("Apply")
        self.apply_button.setToolTip("Apply the selected resolution for the chosen game")
        self.apply_button.clicked.connect(self.apply_resolution)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: green;")

        # Status log text area (optional)
        self.status_log = QTextEdit()
        self.status_log.setReadOnly(True)
        self.status_log.setToolTip("Logs and messages")
        self.status_log.setFixedHeight(100)

        main_layout.addWidget(game_group)
        main_layout.addWidget(res_group)
        main_layout.addWidget(self.apply_button)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.status_log)
        self.setLayout(main_layout)

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
        self.listed_games.insertItem(current_row, f"{current_game} ({self.resolution_combo.currentText()})")

        current_game_path = next((game_path["game"] for game_path in self.list_of_applied_games if get_game_name(game_path["game"]) == current_game), None)        
        if not current_game_path:
            self.status_label.setStyleSheet("color: red;")
            self.status_label.setText("Error: Game path cannot be empty!")
            return

        resolution = self.resolution_combo.currentText()
        game_exists = False
        game_index = -1

        for index, game_config in enumerate(self.list_of_applied_games):
            if game_config["game"] == current_game_path:
                game_exists = True
                game_index = index
                break

        if game_exists:
            # Game exists, edit the resolution
            if self.list_of_applied_games[game_index]["resolution"] == resolution:
                self.status_label.setStyleSheet("color: red;")
                self.status_label.setText("Error: Resolution already applied for this game!")
                return
            self.list_of_applied_games[game_index]["resolution"] = resolution
            status_message = f"Updated resolution to {resolution} for {current_game_path}"
            log_message = f"Updated {current_game_path} with resolution {resolution}."
        else:
            # Game doesn't exist, add new entry
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
            # Remove from list widget.
            row = self.listed_games.row(item)
            self.listed_games.takeItem(row)
            # Remove from in-memory game list.
            if game_name in self.list_of_game:
                self.list_of_game.remove(game_name)
            # Remove any entries in applied games matching this game.
            self.list_of_applied_games = [g for g in self.list_of_applied_games if get_game_name(g["game"]) != game_name]
            self.status_log.append(f"Removed {game_name} from the monitored list.")

        # Update config file.
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
            # Check if game is running
            for process in psutil.process_iter(['name']):
                try:
                    if process.info['name'].lower() == game_name.lower():
                        res = game["resolution"].split(" @ ")
                        width, height = map(int, res[0].split("x"))
                        refresh_rate = int(res[1].replace("Hz", ""))
                        # Change resolution if not applied yet
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameResolutionChanger()
    window.show()
    sys.exit(app.exec())