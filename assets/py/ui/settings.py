from PyQt6.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QRadioButton, QPushButton, QHBoxLayout, QSlider, QLabel, QCheckBox, QComboBox
from PyQt6.QtCore import Qt

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(350, 450)

        layout = QVBoxLayout()

        # Theme settings
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout()
        self.light_theme_radio = QRadioButton("Light")
        self.dark_theme_radio = QRadioButton("Dark")
        
        # Get current theme from parent
        current_theme = "dark"
        if parent:
            current_theme = parent.property("theme")
            if current_theme == "dark":
                self.dark_theme_radio.setChecked(True)
            else:
                self.light_theme_radio.setChecked(True)
        self.apply_theme(current_theme)

        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)

        # AI Parameters
        params_group = QGroupBox("AI Parameters")
        params_layout = QVBoxLayout()
        
        temp_layout = QHBoxLayout()
        temp_label = QLabel("Temperature (Creativity):")
        self.temp_val_label = QLabel("0.7")
        
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 100) # 0.0 to 1.0
        
        current_temp = 0.7
        if parent and hasattr(parent, "current_temperature"):
            current_temp = parent.current_temperature
            
        self.temp_slider.setValue(int(current_temp * 100))
        self.temp_val_label.setText(f"{current_temp:.2f}")
        self.temp_slider.valueChanged.connect(self.on_temp_changed)
        
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_val_label)
        
        params_layout.addLayout(temp_layout)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # TTS Settings
        tts_group = QGroupBox("Text-to-Speech (TTS)")
        tts_layout = QVBoxLayout()
        
        self.tts_enable_cb = QCheckBox("Enable TTS")
        if parent and hasattr(parent, "tts_enabled"):
            self.tts_enable_cb.setChecked(parent.tts_enabled)
        else:
            self.tts_enable_cb.setChecked(True)
        self.tts_enable_cb.toggled.connect(self.on_tts_enable_toggled)
        tts_layout.addWidget(self.tts_enable_cb)
        
        # Voice selection
        voice_layout = QHBoxLayout()
        voice_label = QLabel("Voice:")
        self.voice_combo = QComboBox()
        if parent and hasattr(parent, "speech_engine"):
            voices = parent.speech_engine.availableVoices()
            for voice in voices:
                self.voice_combo.addItem(voice.name())
            current_voice = parent.speech_engine.voice()
            index = self.voice_combo.findText(current_voice.name())
            if index >= 0:
                self.voice_combo.setCurrentIndex(index)
        self.voice_combo.currentIndexChanged.connect(self.on_voice_changed)
        voice_layout.addWidget(voice_label)
        voice_layout.addWidget(self.voice_combo)
        tts_layout.addLayout(voice_layout)
        
        # Pitch
        pitch_layout = QHBoxLayout()
        pitch_label = QLabel("Pitch:")
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(0, 100)
        self.pitch_slider.setValue(50) # Default center (0.0)
        if parent and hasattr(parent, "current_pitch"):
            # Map -1.0...1.0 back to 0...100
            val = int((parent.current_pitch * 50) + 50)
            self.pitch_slider.setValue(val)
        self.pitch_slider.valueChanged.connect(self.on_pitch_changed)
        pitch_layout.addWidget(pitch_label)
        pitch_layout.addWidget(self.pitch_slider)
        tts_layout.addLayout(pitch_layout)
        
        # Rate (Speed)
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Speed:")
        self.rate_slider = QSlider(Qt.Orientation.Horizontal)
        self.rate_slider.setRange(0, 100)
        self.rate_slider.setValue(50) # Default center (0.0)
        if parent and hasattr(parent, "current_rate"):
            # Map -1.0...1.0 back to 0...100
            val = int((parent.current_rate * 50) + 50)
            self.rate_slider.setValue(val)
        self.rate_slider.valueChanged.connect(self.on_rate_changed)
        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.rate_slider)
        tts_layout.addLayout(rate_layout)
        
        # Volume
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume:")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100) # Default max
        if parent and hasattr(parent, "current_volume"):
            # Map 0.0...1.0 to 0...100
            val = int(parent.current_volume * 100)
            self.volume_slider.setValue(val)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        tts_layout.addLayout(volume_layout)
        
        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)

        # Chat history settings
        history_group = QGroupBox("Chat History")
        history_layout = QVBoxLayout()
        self.clear_history_btn = QPushButton("Clear Chat History")
        history_layout.addWidget(self.clear_history_btn)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)

        # Connect signals
        self.light_theme_radio.toggled.connect(self.on_theme_changed)
        self.dark_theme_radio.toggled.connect(self.on_theme_changed)
        self.clear_history_btn.clicked.connect(self.on_clear_history)

        self.setLayout(layout)

    def apply_theme(self, theme):
        if theme == "light":
            self.setStyleSheet("""
                QDialog { background-color: #FFFFFF; color: #1D1B20; font-family: 'Segoe UI', sans-serif; }
                QGroupBox { font-weight: bold; color: #1D1B20; border: 1px solid #E0E0E0; border-radius: 8px; margin-top: 12px; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }
                QRadioButton { color: #1D1B20; }
                QPushButton { background-color: #6750A4; color: white; border-radius: 15px; padding: 8px; }
                QLabel { color: #1D1B20; }
                QCheckBox { color: #1D1B20; }
                QComboBox { background-color: #F3F3F3; color: #1D1B20; border: 1px solid #E0E0E0; border-radius: 4px; padding: 5px; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #141218; color: #E6E1E5; font-family: 'Segoe UI', sans-serif; }
                QGroupBox { font-weight: bold; color: #E6E1E5; border: 1px solid #49454F; border-radius: 8px; margin-top: 12px; }
                QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }
                QRadioButton { color: #E6E1E5; }
                QPushButton { background-color: #4F378B; color: white; border-radius: 15px; padding: 8px; }
                QLabel { color: #E6E1E5; }
                QCheckBox { color: #E6E1E5; }
                QComboBox { background-color: #2B2930; color: #E6E1E5; border: 1px solid #49454F; border-radius: 4px; padding: 5px; }
            """)

    def on_theme_changed(self, checked):
        if checked:
            if self.sender() == self.light_theme_radio:
                theme = "light"
            else:
                theme = "dark"
            
            self.apply_theme(theme)
            if self.parent():
                self.parent().set_theme(theme)

    def on_temp_changed(self, value):
        temp = value / 100.0
        self.temp_val_label.setText(f"{temp:.2f}")
        if self.parent():
            self.parent().set_temperature(temp)
    
    def on_tts_enable_toggled(self, checked):
        if self.parent():
            self.parent().set_tts_enabled(checked)

    def on_voice_changed(self, index):
        if self.parent():
            self.parent().set_tts_voice(index)

    def on_pitch_changed(self, value):
        # Map 0...100 to -1.0...1.0
        pitch = (value - 50) / 50.0
        if self.parent():
            self.parent().set_tts_pitch(pitch)

    def on_rate_changed(self, value):
        # Map 0...100 to -1.0...1.0
        rate = (value - 50) / 50.0
        if self.parent():
            self.parent().set_tts_rate(rate)

    def on_volume_changed(self, value):
        # Map 0...100 to 0.0...1.0
        volume = value / 100.0
        if self.parent():
            self.parent().set_tts_volume(volume)

    def on_clear_history(self):
        self.parent().clear_all_history()
        self.close()
