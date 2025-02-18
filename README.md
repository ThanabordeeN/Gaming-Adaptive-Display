# Gaming Adaptive Display

Gaming Adaptive Display is a Python application that automatically adjusts your display resolution and refresh rate based on the running game. It monitors for game processes and applies the preferred resolution settings when a game is detected.

## Features

- **Dynamic Resolution Change:** Monitors running processes using [`psutil`](https://pypi.org/project/psutil/) and changes the display resolution using custom functions from [`resolution_utils.DEVMODEW`](resolution_utils.py).
- **Graphical User Interface:** Built with [PyQt6](https://pypi.org/project/PyQt6/), featuring game selection, resolution and refresh rate selection, and system tray integration.
- **Game Config Management:** Loads and saves monitored game information from `game_config.json`.
- **Run at Startup:** Supports toggling automatic launch on Windows startup via the Windows registry.
- **Single Instance Check:** Ensures only one instance runs using `QLockFile`.

## Requirements

- Python 3.7+
- [PyQt6](https://pypi.org/project/PyQt6/)
- [psutil](https://pypi.org/project/psutil/)

## Installation

1. Install the required packages:

   ```sh
   pip install PyQt6 psutil
   ```

2. Clone or download the repository.

## Running the Application

Run the application by executing:

```sh
python "Gaming Adaptive Display.py"
```

Alternatively, you can use the provided batch scripts (e.g., build_exe.bat) to create an executable.

## Project Structure

- **Gaming Adaptive Display.py**  
  Main application file with the GUI implementation and process monitoring logic.  
- **resolution_utils.py**  
  Contains utility functions and constants (e.g., `DEVMODEW`, `change_resolution_refresh`) for managing display settings.
- **game_config.json**  
  File used to store the list of monitored games and their selected resolution settings.
- **icon.png**  
  Application icon used in the GUI and system tray.

## Usage

1. **Select or Enter a Game Path:**  
   Use the text editor field or click "Browse" to select a game executable.

2. **Add Game:**  
   When a new game is selected, it is added to the monitored list. The configuration is saved in game_config.json.

3. **Change Resolution:**  
   Choose your desired resolution and refresh rate from the provided drop-down menus and click "Apply". The application will update the display settings when the game is running.

4. **Run at Startup:**  
   Toggle the "Run at Startup" checkbox to add or remove the application from Windows startup.

5. **System Tray:**  
   The app minimizes to the system tray. Double-click the tray icon or use the "Restore" action in the tray menu to bring up the main window.

## License
MIT License
