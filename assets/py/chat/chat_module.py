# chat_module.py
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from google import genai
import openai
import logging

class ChatModule(QObject):
    ai_response = pyqtSignal(str)     # emits AI message
    error_signal = pyqtSignal(str)    # emits crash info

    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    def send_message(self, model, text):
        self.thread = QThread()
        self.worker = ChatWorker(self.api_key, model, text)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.ai_response.emit)
        self.worker.error.connect(self.error_signal.emit)
        self.worker.finished.connect(self.thread.quit)

        self.thread.start()


class ChatWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, api_key, model, text):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.text = text

    def run(self):
        try:
            if "gemini" in self.model:
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model="gemini-3-flash-preview", # Using a known valid model
                    contents=self.text
                )
                self.finished.emit(response.text)

            else:
                openai_client = openai.OpenAI(api_key=self.api_key)
                result = openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": self.text}]
                )
                self.finished.emit(result.choices[0].message.content)

        except Exception as e:
            self.error.emit(str(e))
