import hashlib
import os
import json
import time
from datetime import datetime

HASH_DB = "file_hashes.json"
LOG_FILE = "activity.log"
CHECK_INTERVAL = 10


class FileIntegrityChecker:

    def __init__(self):
        self.hashes = self.load_hashes()

    def normalize_path(self, path):
        return os.path.abspath(path.strip().strip('"'))

    def load_hashes(self):
        if os.path.exists(HASH_DB):
            with open(HASH_DB, 'r') as f:
                return json.load(f)
        return {}

    def save_hashes(self):
        with open(HASH_DB, 'w') as f:
            json.dump(self.hashes, f, indent=4)

    def log(self, message, level="INFO"):
        log_entry = {
            "time": str(datetime.now()),
            "level": level,
            "message": message
        }
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")

    def calculate_hash(self, file_path, algorithm='sha256'):
        if not os.path.exists(file_path):
            return None

        hash_func = hashlib.new(algorithm)

        try:
            with open(file_path, 'rb') as file:
                while True:
                    chunk = file.read(4096)
                    if not chunk:
                        break
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            self.log(f"Error reading file: {file_path} - {e}", "ERROR")
            return None

    def add_file(self, file_path):
        file_path = self.normalize_path(file_path)

        file_hash = self.calculate_hash(file_path)

        if file_hash:
            self.hashes[file_path] = {
                "hash": file_hash,
                "last_checked": str(datetime.now()),
                "size": os.path.getsize(file_path)
            }
            self.save_hashes()
            self.log(f"File added: {file_path}")
            print("✅ File added successfully.")
        else:
            print("❌ Invalid file path.")

    def check_file(self, file_path):
        file_path = self.normalize_path(file_path)

        if file_path not in self.hashes:
            print("⚠ File not monitored.")
            return

        if not os.path.exists(file_path):
            print("❌ File deleted!")
            self.log(f"File deleted: {file_path}", "ALERT")
            return

        current_hash = self.calculate_hash(file_path)
        stored_data = self.hashes[file_path]

        if not current_hash:
            print("❌ Error accessing file.")
            return

        if current_hash == stored_data["hash"]:
            print("✅ File unchanged.")
            self.log(f"Checked OK: {file_path}")
        else:
            print("❌ File modified!")
            self.log(f"File modified: {file_path}", "ALERT")

        self.hashes[file_path]["last_checked"] = str(datetime.now())
        self.save_hashes()

    def check_all_files(self):
        print("\n🔍 Checking all monitored files...\n")
        for file_path in list(self.hashes.keys()):
            print(f"Checking: {file_path}")
            self.check_file(file_path)
            print("-" * 40)

    def monitor(self):
        print(f"\n🚀 Continuous monitoring started (every {CHECK_INTERVAL} seconds)...")
        print("Press Ctrl+C anytime to stop monitoring.\n")

        try:
            while True:
                self.check_all_files()
                time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user.")
            self.log("Monitoring stopped by user", "INFO")


checker = FileIntegrityChecker()

while True:
    print("\n=== FILE INTEGRITY CHECKER (Mini HIDS) ===")
    print("1. Add File")
    print("2. Check File Integrity")
    print("3. Check All Files")
    print("4. Start Continuous Monitoring")
    print("5. Exit")

    choice = input("Enter choice: ")

    if choice == '1':
        path = input("Enter file path: ")
        checker.add_file(path)

    elif choice == '2':
        path = input("Enter file path: ")
        checker.check_file(path)

    elif choice == '3':
        checker.check_all_files()

    elif choice == '4':
        checker.monitor()

    elif choice == '5':
        print("Exiting...")
        break

    else:
        print("❌ Invalid choice!")
