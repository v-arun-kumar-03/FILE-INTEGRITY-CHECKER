class FileIntegrityChecker:

    def __init__(self):
        # Load existing file records into memory when program starts
        self.hashes = self.load_hashes()

    def normalize_path(self, path):
        # Handles messy user input like:  " file.txt "  or  "C:\\file.txt"
        return os.path.abspath(path.strip().strip('"'))

    def load_hashes(self):
        if os.path.exists(HASH_DB):
            with open(HASH_DB, 'r') as f:
                # Converts JSON file → Python dictionary
                return json.load(f)
        return {}

    def save_hashes(self):
        # Converts Python dictionary → JSON file (persistent storage)
        with open(HASH_DB, 'w') as f:
            json.dump(self.hashes, f, indent=4)

    def log(self, message, level="INFO"):
        # Each log entry is stored as a JSON line (easy to parse later)
        log_entry = {
            "time": str(datetime.now()),
            "level": level,
            "message": message
        }
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")  # append mode → keeps history

    def calculate_hash(self, file_path, algorithm='sha256'):
        if not os.path.exists(file_path):
            return None

        # Dynamically creates hash (so you can switch to md5, sha1, etc.)
        hash_func = hashlib.new(algorithm)

        try:
            with open(file_path, 'rb') as file:
                # Loop runs until file.read() returns empty (EOF)
                while True:
                    chunk = file.read(4096)
                    if not chunk:
                        break
                    hash_func.update(chunk)  # updates internal state of hash

            return hash_func.hexdigest()  # final fixed-length fingerprint

        except Exception as e:
            self.log(f"Error reading file: {file_path} - {e}", "ERROR")
            return None

    def add_file(self, file_path):
        file_path = self.normalize_path(file_path)
        file_hash = self.calculate_hash(file_path)

        if file_hash:
            # Overwrites if file already exists → acts like update as well
            self.hashes[file_path] = {
                "hash": file_hash,
                "last_checked": str(datetime.now()),
                "size": os.path.getsize(file_path)  # quick extra validation signal
            }

            self.save_hashes()  # persist immediately (no in-memory risk)
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
            # Important: you don't remove it from DB → so it can be tracked later
            print("❌ File deleted!")
            self.log(f"File deleted: {file_path}", "ALERT")
            return

        current_hash = self.calculate_hash(file_path)
        stored_data = self.hashes[file_path]

        if not current_hash:
            print("❌ Error accessing file.")
            return

        # MAIN DECISION POINT
        # Even 1-bit change → completely different hash
        if current_hash == stored_data["hash"]:
            print("✅ File unchanged.")
            self.log(f"Checked OK: {file_path}")
        else:
            print("❌ File modified!")
            self.log(f"File modified: {file_path}", "ALERT")

        # You are NOT updating stored hash → intentional
        # This keeps original state as baseline
        self.hashes[file_path]["last_checked"] = str(datetime.now())
        self.save_hashes()

    def check_all_files(self):
        print("\n🔍 Checking all monitored files...\n")

        # list() creates a copy → avoids crash if dict changes during loop
        for file_path in list(self.hashes.keys()):
            print(f"Checking: {file_path}")
            self.check_file(file_path)
            print("-" * 40)

    def monitor(self):
        print(f"\n🚀 Continuous monitoring started (every {CHECK_INTERVAL} seconds)...")
        print("Press Ctrl+C anytime to stop monitoring.\n")

        try:
            while True:
                # Infinite loop → behaves like a basic daemon
                self.check_all_files()
                time.sleep(CHECK_INTERVAL)  # controls CPU usage

        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user.")
            self.log("Monitoring stopped by user", "INFO")
