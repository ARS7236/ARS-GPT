import json
import os
from datetime import datetime

HISTORY_DIR = "chat_history"
ARCHIVE_DIR = os.path.join(HISTORY_DIR, "archived")

if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)
if not os.path.exists(ARCHIVE_DIR):
    os.makedirs(ARCHIVE_DIR)

def get_history_files():
    return sorted([f for f in os.listdir(HISTORY_DIR) if f.endswith(".json")])

def save_chat(chat_id, messages):
    file_path = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    with open(file_path, 'w') as f:
        json.dump(messages, f, indent=4)

def load_chat(chat_id):
    file_path = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def create_new_chat_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def archive_chat(chat_id):
    """Moves a chat from the history to the archive."""
    src = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    dst = os.path.join(ARCHIVE_DIR, f"{chat_id}.json")
    if os.path.exists(src):
        os.rename(src, dst)

def delete_chat(chat_id):
    """Deletes a chat file."""
    file_path = os.path.join(HISTORY_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)

def rename_chat(old_chat_id, new_chat_id):
    """Renames a chat file."""
    old_file = os.path.join(HISTORY_DIR, f"{old_chat_id}.json")
    new_file = os.path.join(HISTORY_DIR, f"{new_chat_id}.json")
    if os.path.exists(old_file):
        os.rename(old_file, new_file)
        return True
    return False