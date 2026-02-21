"""
LinkedIn Watcher for AI Employee

Monitors LinkedIn for mentions/posts and auto-posts sales content using Selenium.
"""
import time
import logging
from pathlib import Path
from datetime import datetime
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/linkedin_watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInWatcher:
    """Watches LinkedIn for activity and creates action items."""

    def __init__(self, needs_action_path="Needs_Action", auto_post=True):
        self.needs_action_path = Path(needs_action_path)
        self.processed_posts = set()
        self.processed_mentions = set()
        self.auto_post = auto_post
        self.driver = None

        # LinkedIn credentials (would be retrieved from secure storage in production)
        self.username = os.getenv('LINKEDIN_USERNAME', '')
        self.password = os.getenv('LINKEDIN_PASSWORD', '')

        # Sales content to post (would be dynamically generated in production)
        self.sales_posts = [
            "Looking to improve your business processes? Our AI solutions can help automate your workflow and save time. Contact us for more information!",
            "Did you know that 80% of businesses can reduce administrative tasks by implementing the right AI tools? Let us help you get started!",
            "Success story: We recently helped a company reduce their response time to customer inquiries by 75% through automation. Interested in learning more?",
            "Looking for ways to increase productivity? Our AI Employee solutions offer 24/7 monitoring and automated responses. Get in touch today!"
        ]

        # Create necessary directories
        self.needs_action_path.mkdir(exist_ok=True)
        Path("Logs").mkdir(exist_ok=True)

    def authenticate_linkedin(self):
        """Authenticate with LinkedIn."""
        logger.info("Opening LinkedIn. Please log in if prompted...")

        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Add user agent to look more human-like
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Navigate to LinkedIn
            self.driver.get('https://www.linkedin.com/login')

            # Wait for login page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )

            # Check if already logged in by looking for the search bar
            try:
                self.driver.find_element(By.ID, "global-search-typeahead")
                logger.info("Already logged in to LinkedIn")
                return True
            except:
                pass

            # If not logged in, try to log in
            if self.username and self.password:
                username_field = self.driver.find_element(By.ID, "username")
                username_field.send_keys(self.username)

                password_field = self.driver.find_element(By.ID, "password")
                password_field.send_keys(self.password)

                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()

                # Wait for login to complete
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "global-search-typeahead"))
                )

                logger.info("LinkedIn authentication successful")
                return True
            else:
                logger.warning("No LinkedIn credentials provided. Please log in manually.")
                # Wait for user to manually log in
                time.sleep(30)
                return True

        except Exception as e:
            logger.error(f"Failed to authenticate LinkedIn: {e}")
            return False

    def check_mentions(self):
        """Check for new mentions/notifications."""
        try:
            # Navigate to notifications
            self.driver.get('https://www.linkedin.com/notifications/')

            # Wait for notifications to load
            time.sleep(2)

            # Find notification elements
            notification_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.notification-card")
            new_mentions = []

            for element in notification_elements:
                try:
                    # Extract notification text
                    text_element = element.find_element(By.CSS_SELECTOR, "div.feed-shared-text")
                    text = text_element.text if text_element else "No text found"

                    # Extract timestamp
                    timestamp_element = element.find_element(By.CSS_SELECTOR, "time")
                    timestamp = timestamp_element.get_attribute("datetime") if timestamp_element else datetime.now().isoformat()

                    # Check if this is a mention notification
                    if "mentioned you" in text.lower() or "commented" in text.lower() or "reacted" in text.lower():
                        mention_id = f"mention_{hash(text)}"
                        if mention_id not in self.processed_mentions:
                            mention_data = {
                                'type': 'mention',
                                'content': text,
                                'timestamp': timestamp,
                                'priority': 'medium'
                            }
                            new_mentions.append(mention_data)
                            self.processed_mentions.add(mention_id)
                except NoSuchElementException:
                    continue

            return new_mentions

        except Exception as e:
            logger.error(f"Error checking mentions: {e}")
            return []

    def check_posts(self):
        """Check for new posts on the feed."""
        try:
            # Navigate to home feed
            self.driver.get('https://www.linkedin.com/feed/')

            # Wait for feed to load
            time.sleep(2)

            # Find post elements
            post_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.feed-shared-update-v2")
            new_posts = []

            for element in post_elements:
                try:
                    # Extract post text
                    text_element = element.find_element(By.CSS_SELECTOR, "div.feed-shared-text")
                    text = text_element.text if text_element else "No text found"

                    # Extract author
                    author_element = element.find_element(By.CSS_SELECTOR, "span.feed-shared-actor__name")
                    author = author_element.text if author_element else "Unknown Author"

                    # Extract timestamp
                    timestamp_element = element.find_element(By.CSS_SELECTOR, "span span.time")
                    timestamp = timestamp_element.text if timestamp_element else datetime.now().isoformat()

                    post_id = f"post_{hash(text)}"
                    if post_id not in self.processed_posts:
                        post_data = {
                            'type': 'post',
                            'author': author,
                            'content': text,
                            'timestamp': timestamp,
                            'priority': 'low'
                        }
                        new_posts.append(post_data)
                        self.processed_posts.add(post_id)
                except NoSuchElementException:
                    continue

            return new_posts

        except Exception as e:
            logger.error(f"Error checking posts: {e}")
            return []

    def auto_post_sales_content(self):
        """Auto-post sales content if enabled."""
        if not self.auto_post:
            return False

        try:
            # Navigate to post creation
            self.driver.get('https://www.linkedin.com/post/new/')

            # Wait for post editor to load
            time.sleep(3)

            # Select a random sales post
            import random
            post_content = random.choice(self.sales_posts)

            # Find the post editor and enter content
            post_editor = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
            )

            post_editor.send_keys(post_content)

            # Wait a bit to look human-like
            time.sleep(2)

            # Find and click the post button
            post_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Post']")
            post_button.click()

            logger.info("Successfully posted sales content to LinkedIn")
            return True

        except Exception as e:
            logger.error(f"Error auto-posting to LinkedIn: {e}")
            return False

    def create_action_file(self, activity_data):
        """Create an action file in the Needs_Action folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if activity_data['type'] == 'mention':
            activity_type = "MENTION"
        elif activity_data['type'] == 'post':
            activity_type = "POST"
        else:
            activity_type = "LINKEDIN"

        action_filename = f"LINKEDIN_{activity_type}_{timestamp}_{hash(activity_data['content'][:10])}.md"
        action_filepath = self.needs_action_path / action_filename

        action_content = f"""---
type: linkedin_{activity_data['type']}
priority: {activity_data['priority']}
status: pending
received: {activity_data['timestamp']}
---

# New LinkedIn Activity

## Activity Details
- **Type:** {activity_data['type']}
- **Priority:** {activity_data['priority']}
- **Received:** {activity_data['timestamp']}

## Content
{activity_data['content']}

## Actions Required
- [ ] Review activity content
- [ ] Determine appropriate response based on Company_Handbook.md
- [ ] Respond if necessary (follow approval requirements for LinkedIn posts)
- [ ] Flag for follow-up if needed
- [ ] Move to Done when processed

## Processing Notes
Based on the Company Handbook:
- Sales-generating content should provide value to the audience
- Posts with financial figures require management approval
- Always be professional and polite in interactions
- Follow approval requirements as defined in Approval_Workflow.md
"""

        try:
            action_filepath.write_text(action_content)
            logger.info(f"Created LinkedIn action file: {action_filepath.name}")
            return action_filepath
        except Exception as e:
            logger.error(f"Failed to create action file: {e}")
            return None

    def run(self):
        """Main loop to continuously monitor LinkedIn."""
        # Authenticate first
        if not self.authenticate_linkedin():
            logger.error("Failed to authenticate with LinkedIn. Exiting.")
            return

        logger.info("Starting LinkedIn Watcher...")

        while True:
            try:
                # Check for new mentions
                new_mentions = self.check_mentions()

                # Check for new posts
                new_posts = self.check_posts()

                # Process mentions
                for mention in new_mentions:
                    self.create_action_file(mention)

                # Process posts
                for post in new_posts:
                    self.create_action_file(post)

                # Auto-post sales content periodically (every few hours)
                current_hour = datetime.now().hour
                if current_hour in [9, 12, 15, 18]:  # Post at 9am, 12pm, 3pm, 6pm
                    self.auto_post_sales_content()

                if new_mentions or new_posts:
                    logger.info(f"Processed {len(new_mentions)} mentions and {len(new_posts)} posts")

                # Wait before checking again (check every 5 minutes)
                time.sleep(300)

            except KeyboardInterrupt:
                logger.info("LinkedIn Watcher stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in LinkedIn Watcher: {e}")
                # Wait before retrying to avoid rapid error loops
                time.sleep(60)

        # Clean up
        if self.driver:
            self.driver.quit()

def main():
    """Main function to run the LinkedIn Watcher."""
    try:
        watcher = LinkedInWatcher()
        watcher.run()
    except Exception as e:
        logger.error(f"Failed to start LinkedIn Watcher: {e}")

if __name__ == "__main__":
    main()