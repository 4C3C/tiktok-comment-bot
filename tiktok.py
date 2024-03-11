import pyautogui
import time
import random
import logging
import threading
import requests
import json
import os

class TikTokBot:
    def __init__(self):
        self.load_config()
        self.logger = self.setup_logger()
        self.successful_comments = []
        self.error_count = 0
        self.comment_count = 0
        self.paused = False
        self.lock = threading.Lock()

    def load_config(self):
        try:
            with open('config.json', 'r') as config_file:
                config = json.load(config_file)
                self.webhook_url = config.get('webhook_url', '')
                self.debugging = config.get('debugging', False)
                self.comment_file = config.get('comment_file', 'comment.txt')
                self.comment_button_image = config.get('comment_button_image', 'comment.png')
                self.next_video_button_image = config.get('next_video_button_image', 'click.png')
        except Exception as e:
            print(f"Error loading config.json: {e}")

    def setup_logger(self):
        logger = logging.getLogger("TikTokBot")
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        return logger

    def read_comments(self):
        try:
            with open(self.comment_file, 'r', encoding='utf-8') as file:
                return file.read().splitlines()  # Split lines and return as a list
        except Exception as e:
            self.logger.error(f"Error reading comments from {self.comment_file}: {e}")
            return []

    def locate_center_on_screen(self, image_path):
        try:
            return pyautogui.locateCenterOnScreen(image_path, confidence=0.8)
        except pyautogui.FailSafeException:
            self.logger.error("Failed to locate image due to FailSafeException.")
            return None
        except Exception as e:
            self.logger.error(f"Error locating image {image_path}: {e}")
            return None

    def post_comment(self):
        if self.paused:
            return
        comment_to_post = random.choice(self.read_comments())
        comment_button = self.locate_center_on_screen(self.comment_button_image)
        if comment_button:
            pyautogui.click(comment_button)
            time.sleep(1)
            pyautogui.write(comment_to_post, interval=0.1)  # Write the comment with proper interval
            time.sleep(1)
            pyautogui.press('enter')
            self.lock.acquire()
            self.successful_comments.append(comment_to_post.strip())
            self.comment_count += 1
            self.lock.release()
            time.sleep(2)
            next_video_button = self.locate_center_on_screen(self.next_video_button_image)
            if next_video_button:
                pyautogui.click(next_video_button)
                self.logger.info("Comment posted successfully.")
                self.error_count = 0  # Reset error count
            else:
                self.logger.error("Next video button not found.")
                self.error_count += 1
        else:
            self.logger.error("Comment button not found.")
            self.error_count += 1
        
        if self.error_count >= 5:
            self.logger.error("Constant errors encountered. Stopping the bot.")
            self.send_discord_notification("Due to constant errors, the app has stopped. Please inform developers.")
            self.stop_bot()

    def run_bot(self):
        while True:
            self.post_comment()
            time.sleep(5)  # Delay between posting comments

    def stop_bot(self):
        self.paused = True

    def send_discord_notification(self, message):
        if self.debugging and self.webhook_url:
            payload = {
                "content": message
            }
            try:
                response = requests.post(self.webhook_url, json=payload)
                if response.status_code == 204:
                    self.logger.info("Discord notification sent successfully.")
                else:
                    self.logger.error(f"Failed to send Discord notification. Status code: {response.status_code}")
            except Exception as e:
                self.logger.error(f"Error sending Discord notification: {e}")

def setup_bot():
    print("Welcome to TikTokBot setup!")
    webhook_url = input("Enter your Discord webhook URL: ")
    debugging = input("Enable debugging mode? (y/n): ").lower() == 'y'
    comment_file = input("Enter the path to the comment file (default: comment.txt): ") or 'comment.txt'
    comment_button_image = input("Enter the path to the comment button image (default: comment.png): ") or 'comment.png'
    next_video_button_image = input("Enter the path to the next video button image (default: click.png): ") or 'click.png'

    config = {
        "webhook_url": webhook_url,
        "debugging": debugging,
        "comment_file": comment_file,
        "comment_button_image": comment_button_image,
        "next_video_button_image": next_video_button_image
    }

    with open('config.json', 'w') as config_file:
        json.dump(config, config_file)

if __name__ == "__main__":
    if not os.path.isfile('config.json'):
        setup_bot()
    
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        if not config["webhook_url"]:
            print("Webhook URL not set in config.json. Please run setup again.")
        else:
            bot = TikTokBot()
            bot_thread = threading.Thread(target=bot.run_bot)
            bot_thread.start()
