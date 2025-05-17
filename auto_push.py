import os
import subprocess
import time
import logging
import requests

logging.basicConfig(filename='auto_push.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def check_internet_connection():
    try:
        requests.get('https://github.com', timeout=5)
        return True
    except requests.ConnectionError:
        return False

def git_push():
    try:
        if not check_internet_connection():
            logging.warning("No internet connection. Skipping push.")
            return False

        # Check if there are changes to commit
        status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, check=True)
        if not status.stdout.strip():
            logging.info("No changes to commit.")
            return False

        # Add all changes
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit changes
        commit_message = f'Auto-commit: {time.strftime("%Y-%m-%d %H:%M:%S")}'
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Push changes
        subprocess.run(['git', 'push'], check=True)
        
        logging.info("Changes pushed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred during git operations: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    return False

def watch_and_push(interval=30):  # 30 seconds by default
    last_push_time = 0
    while True:
        try:
            if time.time() - last_push_time >= interval:
                if git_push():
                    last_push_time = time.time()
                    notify_collaborators()
        except Exception as e:
            logging.error(f"Unexpected error in watch_and_push: {e}")
        time.sleep(1)  # Check every 1 second

if __name__ == "__main__":
    watch_and_push()