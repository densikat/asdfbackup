import json
import os
import shutil
import subprocess
import sys


def backup(backup_file):
    print("Backing up asdf plugins and versions...")
    if not shutil.which("asdf"):
        print("asdf is not installed or not in PATH. Exiting.")
        sys.exit(1)

    plugins = []
    result = subprocess.run(["asdf", "plugin", "list"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Failed to list plugins. Exiting.")
        sys.exit(1)

    for plugin in result.stdout.splitlines():
        plugin_data = {"name": plugin, "versions": [], "global": ""}

        # Get current (global) version
        current_result = subprocess.run(["asdf", "current", plugin], capture_output=True, text=True)
        if current_result.returncode == 0:
            # Split the output and get the version, removing any asterisk
            parts = current_result.stdout.split()
            if len(parts) > 1:
                plugin_data["global"] = parts[1].replace('*', '').strip()

        # Get all installed versions
        list_result = subprocess.run(["asdf", "list", plugin], capture_output=True, text=True)
        if list_result.returncode == 0:
            # Clean up version strings: remove asterisks and whitespace
            versions = []
            for line in list_result.stdout.splitlines():
                if line.strip():
                    clean_version = line.replace('*', '').strip()
                    versions.append(clean_version)
            plugin_data["versions"] = versions

        plugins.append(plugin_data)

    with open(backup_file, "w") as f:
        json.dump({"plugins": plugins}, f, indent=2)
    print(f"Backup completed to {backup_file}.")

def restore(backup_file):
    print(f"Restoring asdf plugins and versions from {backup_file}...")
    if not os.path.exists(backup_file):
        print(f"Backup file {backup_file} not found. Exiting.")
        sys.exit(1)
    if not shutil.which("asdf"):
        print("asdf is not installed or not in PATH. Exiting.")
        sys.exit(1)

    with open(backup_file) as f:
        data = json.load(f)

    for plugin in data.get("plugins", []):
        plugin_name = plugin["name"]
        result = subprocess.run(["asdf", "plugin", "list"], capture_output=True, text=True)
        if plugin_name not in result.stdout:
            subprocess.run(["asdf", "plugin", "add", plugin_name], check=True)

        for version in plugin["versions"]:
            subprocess.run(["asdf", "install", plugin_name, version], check=True)

        if plugin["global"]:
            subprocess.run(["asdf", "global", plugin_name, plugin["global"]], check=True)

    print("Restore completed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python asdf_backup_restore.py {backup|restore} [backup_file]")
        sys.exit(1)

    command = sys.argv[1]
    backup_file = sys.argv[2] if len(sys.argv) > 2 else "asdf_plugins_backup.json"

    if command == "backup":
        backup(backup_file)
    elif command == "restore":
        restore(backup_file)
    else:
        print("Invalid command. Use 'backup' or 'restore'.")
        sys.exit(1)
