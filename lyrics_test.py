#!/usr/bin/env python3
import syncedlyrics
import cutlet
import subprocess
import shlex
import time
import json

class PlayerctlMonitor:
    def __init__(self):
        self.process = None
        self.previous_track = {}

    def get_current_metadata(self):
        """Get current metadata as a one-time check"""
        try:
            result = subprocess.run(
                ["playerctl", "metadata", "--format", '{"artist": "{{artist}}", "title": "{{title}}", "album": "{{album}}", "status": "{{status}}"}'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout.strip())
            return None
        except (subprocess.SubprocessError, json.JSONDecodeError) as e:
            print(f"Error getting metadata: {e}")
            return None

    def start_monitoring(self):
        """Start monitoring for track changes"""
        # Command to monitor status and metadata changes
        command = shlex.split("playerctl --follow metadata --format '{{status}},{{artist}},{{title}}'")

        print("Starting media player monitoring...")
        print("Waiting for a track to play...")

        try:
            # Start the process with pipe for stdout
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )

            # Process output as it comes
            for line in iter(self.process.stdout.readline, ''):
                if not line.strip():
                    continue

                try:
                    # Parse the output
                    parts = line.strip().split(',', 2)
                    if len(parts) < 3:
                        continue

                    status, artist, title = parts

                    # Skip if we don't have both artist and title
                    if not artist or not title:
                        continue

                    # Create current track info
                    current_track = {
                        'status': status,
                        'artist': artist,
                        'title': title
                    }

                    # Check if track has changed
                    if current_track != self.previous_track:
                        if status == "Playing":
                            lyr = syncedlyrics.search(f"{title} {artist}")
                            print(lyr)
                        self.previous_track = current_track

                except Exception as e:
                    print(f"Error processing output: {e}")

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
        finally:
            self.stop_monitoring()

    def stop_monitoring(self):
        """Stop the monitoring process"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

if __name__ == "__main__":
    # Check if playerctl is installed
    try:
        version_check = subprocess.run(
            ["playerctl", "--version"],
            capture_output=True,
            text=True
        )
        if version_check.returncode != 0:
            raise Exception("playerctl command not found")

        print(f"Found playerctl version: {version_check.stdout.strip()}")

        # Show current playing track if any
        monitor = PlayerctlMonitor()
        current = monitor.get_current_metadata()
        if current and current.get('status') == 'Playing':
            print(f"Currently playing: {current.get('artist', 'Unknown')} - {current.get('title', 'Unknown')}")

        # Start monitoring
        monitor.start_monitoring()
    except Exception as e:
        print(f"Error: {e}")
        print("Please make sure playerctl is installed. On Ubuntu/Debian: sudo apt install playerctl")
