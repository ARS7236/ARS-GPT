import os
import json

class SearchModule:
    def __init__(self, history_dir):
        self.history_dir = history_dir

    def search(self, query):
        results = []
        if not os.path.exists(self.history_dir):
            return results

        query = query.strip().lower()
        try:
            files = sorted([f for f in os.listdir(self.history_dir) if f.endswith('.json')], reverse=True)
        except OSError:
            return results

        if not query:
            # Return all files with no snippet
            return [{"filename": f, "snippet": None} for f in files]

        for f in files:
            file_path = os.path.join(self.history_dir, f)
            match = False
            snippet = None
            
            # Check filename (display name)
            display_name = f.replace(".json", "")
            parts = display_name.split('_', 2)
            if len(parts) > 2:
                display_name = parts[2]
            
            if query in display_name.lower():
                match = True
            else:
                # Check content
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        for msg in data:
                            msg_text = msg.get('text', '')
                            if query in msg_text.lower():
                                match = True
                                # Create snippet
                                start_idx = msg_text.lower().find(query)
                                start = max(0, start_idx - 15)
                                end = min(len(msg_text), start_idx + len(query) + 15)
                                snippet = "..." + msg_text[start:end].replace("\n", " ") + "..."
                                break
                except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                    continue
            
            if match:
                results.append({"filename": f, "snippet": snippet})
        
        return results