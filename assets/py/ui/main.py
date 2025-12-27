from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QScrollArea, QSizePolicy, QListWidget,
    QFrame, QFileDialog, QMenu, QApplication, QMessageBox, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtTextToSpeech import QTextToSpeech
from assets.py.ui.ui_models import ModelsWindow
from assets.py.chat.chat_module import ChatModule
from assets.py.chat.search_module import SearchModule
from assets.py.ui.settings import SettingsWindow
import json
import os
import base64
import datetime
import re

class ARSGPTMainWindow(QMainWindow):
    ai_response_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARS-GPT (Remastered)")
        self.resize(450, 650)

        self.current_api_key = None
        self.current_model_type = "gpt-4o" # Default fallback
        self.current_temperature = 0.7
        self.chat_module = None
        self.attachment_content = None
        self.attachment_name = None
        self.is_generating = False
        self.chat_messages = []
        self.current_chat_file = None
        self.pending_first_message = None
        self.temp_module = None
        self.speech_engine = QTextToSpeech()
        self.tts_enabled = True
        self.current_pitch = 0.0
        self.current_rate = 0.0
        self.current_volume = 1.0

        # Setup history directories
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.history_dir = os.path.join(base_dir, "chat_history")
        self.archive_dir = os.path.join(self.history_dir, "archive")
        os.makedirs(self.archive_dir, exist_ok=True)
        self.search_module = SearchModule(self.history_dir)

        # --- MAIN CONTAINER ---
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== SIDEBAR =====
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(10, 20, 10, 20)

        self.new_chat_btn = QPushButton("+ New Chat")
        self.new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #4F378B; color: white; border-radius: 16px; 
                padding: 15px; font-weight: bold; text-align: left; padding-left: 20px;
            }
            QPushButton:hover { background-color: #6750A4; }
        """)
        sidebar_layout.addWidget(self.new_chat_btn)

        self.hist_label = QLabel("History")
        sidebar_layout.addWidget(self.hist_label)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search chats...")
        self.search_bar.textChanged.connect(self.filter_chat_history)
        sidebar_layout.addWidget(self.search_bar)

        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.on_history_item_clicked)
        sidebar_layout.addWidget(self.history_list)
        
        self.sidebar.setLayout(sidebar_layout)
        self.sidebar.hide()
        main_layout.addWidget(self.sidebar)

        # ===== CONTENT AREA =====
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)

        # ===== HEADER =====
        header = QHBoxLayout()
        header.setContentsMargins(10, 10, 10, 0)
        self.menu_btn = QPushButton("≡")
        self.menu_btn.setFixedWidth(40)
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.title = QLabel("ARS-GPT")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedWidth(40)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        header.addWidget(self.menu_btn)
        header.addWidget(self.title, 1)
        header.addWidget(self.settings_btn)

        # ===== GREETING =====
        self.greeting = QLabel("Welcome to ARS-GPT!")
        self.greeting.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ===== CHAT AREA =====
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(15)
        self.chat_layout.setContentsMargins(20, 20, 20, 20)
        self.chat_content.setLayout(self.chat_layout)
        self.chat_scroll.setWidget(self.chat_content)

        # ===== INPUT BAR =====
        input_bar = QHBoxLayout()
        input_bar.setContentsMargins(15, 10, 15, 15)
        self.plus_btn = QPushButton("+")
        self.plus_btn.setFixedSize(40, 40)
        self.plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.mode_btn = QPushButton("◎")
        self.mode_btn.setFixedSize(40, 40)
        self.mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText("Ask ARS-GPT")
        
        self.model_btn = QPushButton("Models")
        self.model_btn.setFixedHeight(40)
        self.model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(40, 40)
        
        input_bar.addWidget(self.plus_btn)
        input_bar.addWidget(self.mode_btn)
        input_bar.addWidget(self.prompt, 1)
        input_bar.addWidget(self.model_btn)
        input_bar.addWidget(self.send_btn)

        # ===== ASSEMBLE =====
        content_layout.addLayout(header)
        content_layout.addWidget(self.greeting)
        content_layout.addWidget(self.chat_scroll, 1)
        content_layout.addLayout(input_bar)
        
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # ===== SIGNALS =====
        self.prompt.returnPressed.connect(self.on_send)
        self.prompt.textChanged.connect(self.update_send_button_state)
        self.send_btn.clicked.connect(self.on_toggle_generation)
        self.model_btn.clicked.connect(self.open_models_window)
        self.settings_btn.clicked.connect(self.open_settings)
        self.plus_btn.clicked.connect(self.upload_file)
        self.menu_btn.clicked.connect(self.toggle_sidebar)
        self.new_chat_btn.clicked.connect(self.start_new_chat)
        self.ai_response_signal.connect(self.handle_ai_response)
        
        # Load history
        self.load_chat_history()
        self.load_active_model()
        self.update_send_button_state()
        self.set_theme("dark")

    def closeEvent(self, event):
        # Clean up threads to prevent crash on exit
        if self.chat_module and hasattr(self.chat_module, 'isRunning') and self.chat_module.isRunning():
            self.chat_module.terminate()
            self.chat_module.wait()
        
        if self.temp_module and hasattr(self.temp_module, 'isRunning') and self.temp_module.isRunning():
            self.temp_module.terminate()
            self.temp_module.wait()
        event.accept()

    def update_send_button_state(self):
        if self.is_generating:
            self.send_btn.setEnabled(True)
            self.send_btn.setText("■")
            self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.send_btn.setStyleSheet("background-color: #B3261E; border-radius: 20px; color: white; font-size: 16px; padding-left: 0px;")
            return

        text = self.prompt.text().strip()
        has_attachment = self.attachment_content is not None
        
        if text or has_attachment:
            self.send_btn.setEnabled(True)
            self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.send_btn.setText("➤")
            self.send_btn.setStyleSheet("background-color: #4F378B; border-radius: 20px; color: white; font-size: 20px; padding-left: 3px;")
        else:
            self.send_btn.setEnabled(False)
            self.send_btn.setCursor(Qt.CursorShape.ArrowCursor)
            self.send_btn.setText("➤")
            self.send_btn.setStyleSheet("background-color: #2B2930; border-radius: 20px; color: #555; font-size: 20px; padding-left: 3px;")

    def toggle_sidebar(self):
        if self.sidebar.isVisible():
            self.sidebar.hide()
        else:
            self.sidebar.show()

    def start_new_chat(self):
        # Clear chat layout
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear sub-layout (message container)
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
        
        self.chat_messages = []
        self.current_chat_file = None
        self.pending_first_message = None
        
        self.greeting.show()
        self.prompt.clear()
        if self.sidebar.isVisible():
            self.sidebar.hide()

    def load_chat_history(self):
        self.history_list.clear()
        if os.path.exists(self.history_dir):
            try:
                files = sorted([f for f in os.listdir(self.history_dir) if f.endswith('.json')], reverse=True)
                for f in files:
                    self.add_history_item(f)
            except Exception as e:
                print(f"Error loading history: {e}")

    def filter_chat_history(self, text):
        self.history_list.clear()
        results = self.search_module.search(text)
        for result in results:
            self.add_history_item(result['filename'], result['snippet'])

    def add_history_item(self, filename, snippet=None):
        item = QListWidgetItem()
        height = 65 if snippet else 50
        item.setSizeHint(QSize(0, height))
        item.setData(Qt.ItemDataRole.UserRole, filename)
        
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 5, 5)
        
        # Text container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        # Parse filename for display: YYYYMMDD_HHMMSS_Title.json
        display_name = filename.replace(".json", "")
        parts = display_name.split('_', 2)
        if len(parts) > 2:
            display_name = parts[2]
            
        label = QLabel(display_name)
        label.setStyleSheet("background: transparent; border: none; color: inherit; font-weight: bold;")
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) # Let click pass to list item
        text_layout.addWidget(label)

        if snippet:
            snip_label = QLabel(snippet)
            snip_label.setStyleSheet("background: transparent; border: none; color: #888888; font-size: 11px;")
            snip_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            text_layout.addWidget(snip_label)
        else:
            text_layout.addStretch()
        
        layout.addLayout(text_layout)
        layout.addStretch()

        menu_btn = QPushButton("⋮")
        menu_btn.setFixedSize(24, 24)
        menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        menu_btn.setStyleSheet("""
            QPushButton { background: transparent; border: none; color: inherit; font-weight: bold; border-radius: 12px; }
            QPushButton:hover { background-color: rgba(128, 128, 128, 0.3); }
        """)
        menu_btn.clicked.connect(lambda: self.show_history_menu(menu_btn, filename, item))
        
        layout.addWidget(menu_btn)
        widget.setLayout(layout)
        
        self.history_list.addItem(item)
        self.history_list.setItemWidget(item, widget)

    def show_history_menu(self, btn, filename, item):
        menu = QMenu(self)
        delete_action = menu.addAction("Delete")
        archive_action = menu.addAction("Archive")
        
        # Style the menu
        menu.setStyleSheet("""
            QMenu { background-color: #2B2930; color: #E6E1E5; border: 1px solid #49454F; }
            QMenu::item { padding: 8px 20px; }
            QMenu::item:selected { background-color: #4F378B; }
        """)
        
        action = menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        
        if action == delete_action:
            self.delete_chat(filename, item)
        elif action == archive_action:
            self.archive_chat(filename, item)

    def delete_chat(self, filename, item):
        path = os.path.join(self.history_dir, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except: pass
        
        row = self.history_list.row(item)
        self.history_list.takeItem(row)
        
        if self.current_chat_file == path:
            self.start_new_chat()

    def archive_chat(self, filename, item):
        src = os.path.join(self.history_dir, filename)
        dst = os.path.join(self.archive_dir, filename)
        if os.path.exists(src):
            try:
                os.rename(src, dst)
            except: pass
            
        row = self.history_list.row(item)
        self.history_list.takeItem(row)
        
        if self.current_chat_file == src:
            self.start_new_chat()

    def on_history_item_clicked(self, item):
        filename = item.data(Qt.ItemDataRole.UserRole)
        path = os.path.join(self.history_dir, filename)
        
        if not os.path.exists(path):
            return
            
        # Clear current UI without resetting file logic yet
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
                item.layout().deleteLater()
            
        self.greeting.hide()
        self.current_chat_file = path
        self.chat_messages = []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.chat_messages = data
                for msg in data:
                    self.render_message(msg['text'], msg['sender'])
            
            # Scroll to bottom
            QTimer.singleShot(100, lambda: self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()))
        except Exception as e:
            print(f"Error loading chat: {e}")

    # ===== CHAT FUNCTIONS =====
    def add_message(self, text, sender='user'):
        bubble = self.render_message(text, sender)
        
        # Save to memory and file
        self.chat_messages.append({"sender": sender, "text": text})
        if self.current_chat_file:
            self.save_chat()
            
        return bubble

    def render_complex_message(self, text, sender):
        bubble = QWidget()
        bubble.setProperty("sender", sender)
        bubble.setProperty("original_text", text)
        
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Split text by code blocks
        parts = re.split(r"```(\w*)\n(.*?)```", text, flags=re.DOTALL)
        
        i = 0
        while i < len(parts):
            content = parts[i].strip()
            if content:
                lbl = QLabel(content)
                lbl.setTextFormat(Qt.TextFormat.MarkdownText)
                lbl.setWordWrap(True)
                lbl.setOpenExternalLinks(True)
                lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                lbl.setStyleSheet("background: transparent; color: #E6E1E5; font-size: 14px;")
                layout.addWidget(lbl)
            
            if i + 2 < len(parts):
                lang = parts[i+1].strip()
                code = parts[i+2].strip()
                
                # Canvas Container
                canvas = QFrame()
                canvas.setStyleSheet("background-color: #1E1E1E; border-radius: 8px; border: 1px solid #49454F;")
                canvas_layout = QVBoxLayout(canvas)
                canvas_layout.setContentsMargins(0, 0, 0, 0)
                canvas_layout.setSpacing(0)
                
                # Header
                header_widget = QWidget()
                header_widget.setStyleSheet("background-color: #2D2D2D; border-top-left-radius: 8px; border-top-right-radius: 8px;")
                header_layout = QHBoxLayout(header_widget)
                header_layout.setContentsMargins(10, 5, 10, 5)
                
                lang_label = QLabel(f"Canvas ({lang})" if lang else "Canvas")
                lang_label.setStyleSheet("color: #A0A0A0; font-weight: bold; font-size: 12px; border: none; background: transparent;")
                header_layout.addWidget(lang_label)
                
                header_layout.addStretch()
                
                copy_btn = QPushButton("Copy Code")
                copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                copy_btn.setStyleSheet("QPushButton { color: #A0A0A0; border: none; font-weight: bold; font-size: 12px; background: transparent; } QPushButton:hover { color: #FFFFFF; }")
                copy_btn.clicked.connect(lambda checked, c=code: QApplication.clipboard().setText(c))
                header_layout.addWidget(copy_btn)
                
                canvas_layout.addWidget(header_widget)
                
                # Code Body
                code_lbl = QLabel(code)
                code_lbl.setTextFormat(Qt.TextFormat.PlainText)
                code_lbl.setStyleSheet("color: #D4D4D4; font-family: 'Consolas', 'Monaco', monospace; padding: 10px; font-size: 13px; background: transparent;")
                code_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                code_lbl.setWordWrap(True)
                canvas_layout.addWidget(code_lbl)
                
                layout.addWidget(canvas)
                i += 3
            else:
                i += 1
        
        # Apply AI Bubble Style
        bubble.setStyleSheet("""
            QWidget { background-color: #332D41; color: #E6E1E5; border-radius: 20px; border-bottom-left-radius: 4px; }
        """)
        
        bubble.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        bubble.customContextMenuRequested.connect(lambda pos: self.show_message_context_menu(pos, bubble))
        
        container = QHBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.addWidget(bubble)
        
        tts_btn = QPushButton("🔊")
        tts_btn.setFixedSize(30, 30)
        tts_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tts_btn.setStyleSheet("background: transparent; border: none; font-size: 16px; color: #E6E1E5;")
        tts_btn.setToolTip("Read Aloud")
        tts_btn.clicked.connect(lambda checked, t=text: self.speak_text(t))
        container.addWidget(tts_btn)
        
        container.addStretch()
        
        self.chat_layout.addLayout(container)
        QTimer.singleShot(10, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()))
        return bubble

    def render_message(self, text, sender):
        if sender == 'ai' and "```" in text:
            return self.render_complex_message(text, sender)
            
        bubble = QLabel()
        bubble.setTextFormat(Qt.TextFormat.MarkdownText)
        bubble.setText(text)
        bubble.setOpenExternalLinks(True)
        bubble.setWordWrap(True)
        if sender == 'user':
            bubble.setMaximumWidth(350)
        bubble.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        bubble.setProperty("sender", sender)
        bubble.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        bubble.customContextMenuRequested.connect(lambda pos: self.show_message_context_menu(pos, bubble))

        if sender == 'user':
            # Material You Primary Container (Right side)
            bubble.setStyleSheet("""
                background-color: #4F378B; 
                color: #FFFFFF; 
                padding: 12px 16px; 
                border-radius: 20px;
                border-bottom-right-radius: 4px;
                font-size: 14px;
            """)
        else:
            # Material You Surface Variant (Left side)
            bubble.setStyleSheet("""
                background-color: #332D41; 
                color: #E6E1E5; 
                padding: 12px 16px; 
                border-radius: 20px;
                border-bottom-left-radius: 4px;
                font-size: 14px;
            """)

        container = QHBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        if sender == 'user':
            container.addStretch()
            container.addWidget(bubble)
        else:
            container.addWidget(bubble)
            
            tts_btn = QPushButton("🔊")
            tts_btn.setFixedSize(30, 30)
            tts_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            tts_btn.setStyleSheet("background: transparent; border: none; font-size: 16px; color: #E6E1E5;")
            tts_btn.setToolTip("Read Aloud")
            tts_btn.clicked.connect(lambda checked, t=text: self.speak_text(t))
            container.addWidget(tts_btn)
            
            container.addStretch()
            
        self.chat_layout.addLayout(container)
        # Scroll to bottom after layout update to prevent rendering glitches
        QTimer.singleShot(10, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()))
        return bubble

    def speak_text(self, text):
        if not self.tts_enabled:
            return
            
        if self.speech_engine.state() == QTextToSpeech.State.Speaking:
            self.speech_engine.stop()
        else:
            # Basic markdown stripping to avoid reading symbols
            clean_text = re.sub(r'[*_`#]', '', text)
            self.speech_engine.say(clean_text)

    def set_tts_enabled(self, enabled):
        self.tts_enabled = enabled
        if not enabled:
            self.speech_engine.stop()

    def set_tts_voice(self, index):
        voices = self.speech_engine.availableVoices()
        if 0 <= index < len(voices):
            self.speech_engine.setVoice(voices[index])

    def set_tts_pitch(self, value):
        self.current_pitch = value
        self.speech_engine.setPitch(value)

    def set_tts_rate(self, value):
        self.current_rate = value
        self.speech_engine.setRate(value)

    def set_tts_volume(self, value):
        self.current_volume = value
        self.speech_engine.setVolume(value)

    def save_chat(self):
        if self.current_chat_file:
            try:
                with open(self.current_chat_file, 'w', encoding='utf-8') as f:
                    json.dump(self.chat_messages, f, indent=4)
            except Exception as e:
                print(f"Error saving chat: {e}")

    def show_message_context_menu(self, pos, bubble):
        menu = QMenu(self)
        sender = bubble.property("sender")
        
        # Actions
        if sender == 'user':
            if self.is_last_user_message(bubble):
                edit_action = menu.addAction("Edit")
                edit_action.triggered.connect(lambda: self.edit_user_message(bubble))
        
        copy_action = menu.addAction("Copy")
        
        # Handle copy for both simple labels and complex widgets
        text = bubble.property("original_text")
        if text is None and hasattr(bubble, "text"):
            text = bubble.text()
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(text or ""))
        
        if sender == 'ai':
            if self.is_last_message(bubble):
                regen_action = menu.addAction("Regenerate")
                regen_action.triggered.connect(lambda: self.regenerate_response(bubble))
            think_action = menu.addAction("Show thinking process")
            think_action.triggered.connect(lambda: self.show_thinking_process())
            
        menu.setStyleSheet("""
            QMenu { background-color: #2B2930; color: #E6E1E5; border: 1px solid #49454F; }
            QMenu::item { padding: 8px 20px; }
            QMenu::item:selected { background-color: #4F378B; }
        """)
        menu.exec(bubble.mapToGlobal(pos))

    def is_last_user_message(self, bubble):
        index = self.get_bubble_layout_index(bubble)
        if index == -1: return False
        
        # Check subsequent messages for any user messages
        for i in range(index + 1, self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item and item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if isinstance(widget, QLabel) and widget.property("sender") == "user":
                        return False
        return True

    def is_last_message(self, bubble):
        return self.get_bubble_layout_index(bubble) == self.chat_layout.count() - 1

    def get_bubble_layout_index(self, bubble):
        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item.layout():
                for j in range(item.layout().count()):
                    if item.layout().itemAt(j).widget() == bubble:
                        return i
        return -1

    def edit_user_message(self, bubble):
        self.prompt.setText(bubble.text())
        self.prompt.setFocus()
        self.remove_messages_from(bubble)

    def regenerate_response(self, ai_bubble):
        ai_index = self.get_bubble_layout_index(ai_bubble)
        if ai_index == -1: return
        
        user_text = None
        # Find preceding user message
        for i in range(ai_index - 1, -1, -1):
            item = self.chat_layout.itemAt(i)
            if item.layout():
                for j in range(item.layout().count()):
                    widget = item.layout().itemAt(j).widget()
                    if isinstance(widget, QLabel) and widget.property("sender") == "user":
                        user_text = widget.property("full_prompt")
                        if not user_text:
                            user_text = widget.text()
                        break
            if user_text: break
            
        if user_text:
            self.remove_messages_from(ai_bubble)
            self.is_generating = True
            self.update_send_button_state()
            self.get_ai_response(user_text)

    def show_thinking_process(self):
        QMessageBox.information(self, "Thinking Process", "Thinking process data is not available for this message.")

    def remove_messages_from(self, bubble):
        index = self.get_bubble_layout_index(bubble)
        if index != -1:
            # Remove this and all subsequent messages
            while self.chat_layout.count() > index:
                item = self.chat_layout.takeAt(index)
                if item.layout():
                    while item.layout().count():
                        sub_item = item.layout().takeAt(0)
                        if sub_item.widget():
                            sub_item.widget().deleteLater()
                    item.layout().deleteLater()

    def upload_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', '', "All Files (*);;Images (*.png *.jpg *.jpeg *.gif *.webp);;Text files (*.txt *.md *.py *.json *.csv)")
        if fname:
            try:
                self.attachment_name = os.path.basename(fname)
                try:
                    with open(fname, 'r', encoding='utf-8') as f:
                        self.attachment_content = f.read()
                except UnicodeDecodeError:
                    with open(fname, 'rb') as f:
                        self.attachment_content = f"Base64 Encoded Media ({self.attachment_name}):\n{base64.b64encode(f.read()).decode('utf-8')}"
                self.plus_btn.setStyleSheet("background-color: #4F378B; border-radius: 20px; color: white; font-size: 20px;")
                self.prompt.setPlaceholderText(f"Ask about {self.attachment_name}...")
                self.update_send_button_state()
            except Exception as e:
                self.add_message(f"Error reading file: {e}", 'ai')

    def on_toggle_generation(self):
        if self.is_generating:
            self.stop_generation()
        else:
            self.on_send()

    def on_send(self):
        if self.is_generating:
            return
            
        text = self.prompt.text().strip()
        
        if (not text and not self.attachment_content) or not self.current_api_key:
            return
            
        display_text = text
        full_prompt = text

        if self.attachment_content:
            display_text = f"📎 {self.attachment_name}\n{text}" if text else f"📎 {self.attachment_name}"
            full_prompt = f"Here is a file content ({self.attachment_name}):\n\n{self.attachment_content}\n\nUser: {text}"
            
            # Reset attachment
            self.attachment_content = None
            self.attachment_name = None
            self.plus_btn.setStyleSheet("background-color: #2B2930; border-radius: 20px; color: #CAC4D0; font-size: 20px;")
            self.prompt.setPlaceholderText("Ask ARS-GPT")

        # Handle New Chat (Title Generation)
        if not self.current_chat_file:
            self.pending_first_message = full_prompt
            
            # Show user message immediately
            user_bubble = self.add_message(display_text, 'user')
            user_bubble.setProperty("full_prompt", full_prompt)
            if self.greeting.isVisible(): self.greeting.hide()
            self.prompt.clear()
            
            self.is_generating = True
            self.update_send_button_state()
            
            # Generate Title
            self.generate_chat_title(text)
            return

        user_bubble = self.add_message(display_text, 'user')
        user_bubble.setProperty("full_prompt", full_prompt)
        if self.greeting.isVisible():
            self.greeting.hide()
        self.prompt.clear()
        self.update_send_button_state()
        
        self.is_generating = True
        self.update_send_button_state()
        self.get_ai_response(full_prompt)

    def generate_chat_title(self, first_message):
        # Clean up previous temp_module if it exists
        if self.temp_module and hasattr(self.temp_module, 'isRunning') and self.temp_module.isRunning():
            self.temp_module.terminate()
            self.temp_module.wait()
            
        # Use a temporary ChatModule to avoid polluting the main context
        self.temp_module = ChatModule(self.current_api_key)
        self.temp_module.ai_response.connect(self.handle_title_response)
        self.temp_module.error_signal.connect(self.handle_title_error)
        
        prompt = f"Generate a very short, concise title (max 5 words) for a chat that starts with this message: '{first_message}'. Return ONLY the title, no quotes."
        self.temp_module.send_message(self.current_model_type, prompt)

    def handle_title_response(self, title):
        title = title.strip().replace('"', '').replace("'", "").replace("/", "-").replace("\\", "-").replace(":", "-")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{title}.json"
        self.current_chat_file = os.path.join(self.history_dir, filename)
        
        # Save the first message (which was already added to chat_messages)
        self.save_chat()
        
        # Add to sidebar (insert at top)
        self.history_list.clear() # Refresh list to ensure order or just insert
        self.load_chat_history()
        
        # Proceed with actual response
        if self.pending_first_message:
            self.get_ai_response(self.pending_first_message)
            self.pending_first_message = None

    def handle_title_error(self, error):
        # Fallback if title generation fails
        self.handle_title_response("New Chat")

    def stop_generation(self):
        self.is_generating = False
        self.update_send_button_state()
        self.add_message("Generation stopped.", 'ai')

    def handle_ai_response(self, text):
        if self.is_generating:
            self.is_generating = False
            self.update_send_button_state()
            self.add_message(text, 'ai')

    def handle_error(self, error_msg):
        self.is_generating = False
        self.update_send_button_state()
        self.add_message(f"Error: {error_msg}", 'ai')

    def get_ai_response(self, prompt):
        if not self.current_api_key:
            self.add_message("Please select an AI model and provide an API key first.", 'ai')
            return

        # Initialize or update ChatModule
        if self.chat_module is None:
            self.chat_module = ChatModule(self.current_api_key)
            self.chat_module.ai_response.connect(self.handle_ai_response)
            self.chat_module.error_signal.connect(self.handle_error)
        else:
            self.chat_module.api_key = self.current_api_key

        # Send message using the active model type
        self.chat_module.send_message(self.current_model_type, prompt)

    def load_active_model(self):
        # Calculate path to api/models.json
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        models_file = os.path.join(base_dir, 'api', 'models.json')
        
        if os.path.exists(models_file):
            try:
                with open(models_file, 'r') as f:
                    data = json.load(f)
                    for name, info in data.items():
                        if info.get("state") == "active":
                            self.current_api_key = info.get("key")
                            # Determine model type based on name
                            if "Google" in name: self.current_model_type = "gemini"
                            elif "OpenAI" in name: self.current_model_type = "gpt-4o"
                            elif "DeepSeek" in name: self.current_model_type = "deepseek-chat"
                            break
            except Exception as e:
                print(f"Error loading active model: {e}")

    # ===== MODELS WINDOW =====
    def open_models_window(self):
        dialog = ModelsWindow(self)
        if dialog.exec():
            # Reload model info from file to get both key and model type
            self.load_active_model()
            print(f"Active Model: {self.current_model_type}")

    # ===== SETTINGS FUNCTIONS =====
    def open_settings(self):
        settings = SettingsWindow(self)
        settings.exec()

    def set_temperature(self, value):
        self.current_temperature = value
        if self.chat_module:
            self.chat_module.temperature = value

    def set_theme(self, theme):
        self.setProperty("theme", theme)
        if theme == "light":
            self.setStyleSheet("""
                QMainWindow { background-color: #FFFFFF; }
                QWidget { color: #1D1B20; font-family: 'Segoe UI', 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif; font-size: 14px; }
                QLineEdit { background-color: #F3F3F3; border: none; border-radius: 24px; padding: 12px 20px; color: #1D1B20; }
                QScrollArea { border: none; background: transparent; }
                QScrollBar:vertical { border: none; background: #FFFFFF; width: 8px; margin: 0; }
                QScrollBar::handle:vertical { background: #E0E0E0; min-height: 20px; border-radius: 4px; }
            """)
            
            self.menu_btn.setStyleSheet("background: transparent; font-size: 24px; color: #1D1B20;")
            self.title.setStyleSheet("font-weight: bold; font-size: 18px; color: #1D1B20;")
            self.settings_btn.setStyleSheet("background: transparent; font-size: 20px; color: #1D1B20;")
            self.greeting.setStyleSheet("font-size: 24px; color: #1D1B20; margin-top: 40px;")
            
            self.plus_btn.setStyleSheet("background-color: #F3F3F3; border-radius: 20px; color: #1D1B20; font-size: 20px;")
            self.mode_btn.setStyleSheet("background-color: #F3F3F3; border-radius: 20px; color: #1D1B20; font-size: 18px;")
            self.model_btn.setStyleSheet("background-color: #F3F3F3; border-radius: 20px; padding: 0 15px; color: #1D1B20;")
            
            self.sidebar.setStyleSheet("background-color: #F3F3F3; border-right: 1px solid #E0E0E0;")
            self.hist_label.setStyleSheet("font-size: 12px; margin-top: 20px; margin-bottom: 5px; padding-left: 10px; border: none; color: #1D1B20;")
            self.history_list.setStyleSheet("""
                QListWidget { border: none; background: transparent; }
                QListWidget::item { padding: 12px; border-radius: 24px; color: #1D1B20; margin-bottom: 4px; }
                QListWidget::item:hover { background-color: #E0E0E0; }
                QListWidget::item:selected { background-color: #D0D0D0; }
            """)
            self.search_bar.setStyleSheet("""
                background-color: #E0E0E0; color: #1D1B20; border: none; border-radius: 15px; padding: 8px 12px; margin-bottom: 5px;
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #141218; }
                QWidget { color: #E6E1E5; font-family: 'Segoe UI', 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif; font-size: 14px; }
                QLineEdit { background-color: #2B2930; border: none; border-radius: 24px; padding: 12px 20px; color: #E6E1E5; }
                QScrollArea { border: none; background: transparent; }
                QScrollBar:vertical { border: none; background: #141218; width: 8px; margin: 0; }
                QScrollBar::handle:vertical { background: #49454F; min-height: 20px; border-radius: 4px; }
            """)
            
            self.menu_btn.setStyleSheet("background: transparent; font-size: 24px; color: #E6E1E5;")
            self.title.setStyleSheet("font-weight: bold; font-size: 18px; color: #E6E1E5;")
            self.settings_btn.setStyleSheet("background: transparent; font-size: 20px; color: #E6E1E5;")
            self.greeting.setStyleSheet("font-size: 24px; color: #CAC4D0; margin-top: 40px;")
            
            self.plus_btn.setStyleSheet("background-color: #2B2930; border-radius: 20px; color: #CAC4D0; font-size: 20px;")
            self.mode_btn.setStyleSheet("background-color: #2B2930; border-radius: 20px; color: #CAC4D0; font-size: 18px;")
            self.model_btn.setStyleSheet("background-color: #2B2930; border-radius: 20px; padding: 0 15px; color: #E6E1E5;")
            
            self.sidebar.setStyleSheet("background-color: #1D1B20; border-right: 1px solid #333;")
            self.hist_label.setStyleSheet("font-size: 12px; margin-top: 20px; margin-bottom: 5px; padding-left: 10px; border: none; color: #CAC4D0;")
            self.history_list.setStyleSheet("""
                QListWidget { border: none; background: transparent; }
                QListWidget::item { padding: 12px; border-radius: 24px; color: #E6E1E5; margin-bottom: 4px; }
                QListWidget::item:hover { background-color: #332D41; }
                QListWidget::item:selected { background-color: #4A4458; }
            """)
            self.search_bar.setStyleSheet("""
                background-color: #332D41; color: #E6E1E5; border: none; border-radius: 15px; padding: 8px 12px; margin-bottom: 5px;
            """)

    def clear_all_history(self):
        # This needs to be updated to handle the new file structure if needed, 
        # but the existing implementation deletes all .json files in chat_history, which is still valid.
        # We just need to reset the current chat state.
        if os.path.exists(self.history_dir):
            for f in os.listdir(self.history_dir):
                if f.endswith('.json'):
                    try:
                        os.remove(os.path.join(self.history_dir, f))
                    except: pass
        self.history_list.clear()
        self.start_new_chat()
