import json
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, 
    QPushButton, QHBoxLayout, QWidget, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt

# Calculate path to api/models.json relative to this file
# assets/py/ui/ui_models.py -> ... -> api/models.json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODELS_FILE = os.path.join(BASE_DIR, 'api', 'models.json')

class AddModelDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Model")
        self.resize(350, 280)
        self.setStyleSheet("""
            QDialog { background-color: #141218; color: #E6E1E5; font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #E6E1E5; font-size: 14px; font-weight: bold; }
            QComboBox, QLineEdit { 
                background-color: #2B2930; color: #E6E1E5; border: none; 
                padding: 12px; border-radius: 8px; font-size: 14px;
            }
            QComboBox::drop-down { border: none; }
            QPushButton {
                background-color: #4F378B; color: white; border-radius: 20px; 
                padding: 10px 20px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #6750A4; }
            QLabel#hint { color: #CAC4D0; font-size: 12px; font-weight: normal; margin-bottom: 5px; }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        layout.addWidget(QLabel("Which one?"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Google", "OpenAI", "Claude", "DeepSeek"])
        self.provider_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.provider_combo.currentIndexChanged.connect(self.update_hint)
        layout.addWidget(self.provider_combo)

        self.hint_label = QLabel()
        self.hint_label.setObjectName("hint")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Paste API Key here...")
        layout.addWidget(self.key_input)

        layout.addStretch()

        add_btn = QPushButton("Add")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.accept)
        layout.addWidget(add_btn)

        self.setLayout(layout)
        self.update_hint()

    def update_hint(self):
        provider = self.provider_combo.currentText()
        hints = {
            "Google": "Example: AIzaSy...",
            "OpenAI": "Example: sk-proj-...",
            "Claude": "Example: sk-ant-...",
            "DeepSeek": "Example: sk-..."
        }
        self.hint_label.setText(hints.get(provider, "Enter API Key"))

    def get_data(self):
        return self.provider_combo.currentText(), self.key_input.text().strip()

class ModelItem(QFrame):
    def __init__(self, name, key, is_active, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.name = name
        self.setStyleSheet("""
            QFrame {
                background-color: #2B2930;
                border-radius: 16px;
            }
            QLabel { background: transparent; border: none; }
            QPushButton {
                border-radius: 18px;
                font-weight: bold;
                padding: 8px 16px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #E6E1E5;")
        
        # Mask key for display
        masked_key = f"{key[:6]}...{key[-4:]}" if len(key) > 10 else "******"
        key_lbl = QLabel(masked_key)
        key_lbl.setStyleSheet("font-size: 12px; color: #CAC4D0;")
        
        info_layout.addWidget(name_lbl)
        info_layout.addWidget(key_lbl)
        layout.addLayout(info_layout)
        
        layout.addStretch()
        
        self.toggle_btn = QPushButton()
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedSize(80, 36)
        self.update_state(is_active)
        self.toggle_btn.clicked.connect(self.on_toggle)
        
        layout.addWidget(self.toggle_btn)
        self.setLayout(layout)

    def update_state(self, is_active):
        if is_active:
            self.toggle_btn.setText("Active")
            self.toggle_btn.setStyleSheet("background-color: #4F378B; color: #FFFFFF;")
        else:
            self.toggle_btn.setText("Enable")
            self.toggle_btn.setStyleSheet("background-color: #1D1B20; color: #E6E1E5; border: 1px solid #49454F;")

    def on_toggle(self):
        self.parent_window.set_active(self.name)

class ModelsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Models")
        self.resize(400, 500)
        self.setStyleSheet("background-color: #141218;")
        
        self.models = {}
        self.load_models()

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("AI Models")
        title.setStyleSheet("color: #E6E1E5; font-size: 22px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Add Button
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedSize(40, 40)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F378B; color: white; 
                border-radius: 20px; font-size: 24px; padding-bottom: 4px;
            }
            QPushButton:hover { background-color: #6750A4; }
        """)
        self.add_btn.clicked.connect(self.open_add_dialog)
        header_layout.addWidget(self.add_btn)
        layout.addLayout(header_layout)

        # List
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout()
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setSpacing(10)
        self.container.setLayout(self.list_layout)
        self.scroll.setWidget(self.container)
        
        layout.addWidget(self.scroll)
        
        # Close Button
        close_btn = QPushButton("Done")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B2930; color: #E6E1E5; 
                border-radius: 20px; padding: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #49454F; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)
        self.refresh_ui()

    def load_models(self):
        if os.path.exists(MODELS_FILE):
            try:
                with open(MODELS_FILE, 'r') as f:
                    self.models = json.load(f)
            except Exception as e:
                print(f"Error loading models: {e}")
                self.models = {}
        else:
            self.models = {}

    def save_models(self):
        try:
            os.makedirs(os.path.dirname(MODELS_FILE), exist_ok=True)
            with open(MODELS_FILE, 'w') as f:
                json.dump(self.models, f, indent=4)
        except Exception as e:
            print(f"Error saving models: {e}")

    def refresh_ui(self):
        # Clear list
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.models:
            empty_lbl = QLabel("No models found.\nClick + to add one.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #777; font-size: 14px; margin-top: 50px;")
            self.list_layout.addWidget(empty_lbl)
            return

        for name, data in self.models.items():
            is_active = (data.get("state") == "active")
            item = ModelItem(name, data.get("key", ""), is_active, self)
            self.list_layout.addWidget(item)

    def set_active(self, active_name):
        for name in self.models:
            if name == active_name:
                self.models[name]["state"] = "active"
            else:
                self.models[name]["state"] = "disabled"
        self.save_models()
        
        # Update UI in place instead of rebuilding (prevents QPainter errors)
        for i in range(self.list_layout.count()):
            widget = self.list_layout.itemAt(i).widget()
            if isinstance(widget, ModelItem):
                widget.update_state(widget.name == active_name)

    def open_add_dialog(self):
        dialog = AddModelDialog(self)
        if dialog.exec():
            provider, key = dialog.get_data()
            if key:
                # Generate name
                base_name = f"{provider} key"
                name = base_name
                count = 1
                while name in self.models:
                    count += 1
                    name = f"{base_name} ({count})"
                
                # If first model, make active
                state = "active" if not self.models else "disabled"
                
                self.models[name] = {
                    "key": key,
                    "state": state
                }
                self.save_models()
                self.refresh_ui()

    def get_selected_key(self):
        for data in self.models.values():
            if data.get("state") == "active":
                return data.get("key")
        return None
