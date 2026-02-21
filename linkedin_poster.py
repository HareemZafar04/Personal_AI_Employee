"""
LinkedIn Poster for AI Employee

Automatically posts updates to LinkedIn to generate sales.
"""
import time
import logging
from pathlib import Path
from datetime import datetime
import requests
import json
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/linkedin_poster.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInPoster:
    """Handles posting to LinkedIn for business promotion."""

    def __init__(self, access_token=None):
        self.access_token = access_token or self._get_access_token()
        self.api_base_url = "https://api.linkedin.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        self.business_updates_path = "/ugcPosts"

    def _get_access_token(self):
        """Get LinkedIn access token from environment or file."""
        # Try to get from environment variable first
        import os
        token = os.getenv('LINKEDIN_ACCESS_TOKEN')

        if not token:
            # Try to read from a config file
            config_path = Path('linkedin_config.json')
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    token = config.get('access_token')

        if not token:
            raise ValueError("LinkedIn access token not found. Please set LINKEDIN_ACCESS_TOKEN environment variable or create linkedin_config.json")

        return token

    def create_text_post(self, text: str, visibility: str = "PUBLIC") -> Dict:
        """Create a text-based LinkedIn post."""
        try:
            # Create the UGC post (User Generated Content)
            post_data = {
                "author": f"urn:li:person:{self._get_person_urn_id()}",  # This needs to be the person's URN
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }

            response = requests.post(
                f"{self.api_base_url}{self.business_updates_path}",
                headers=self.headers,
                json=post_data
            )

            if response.status_code == 201:
                logger.info("LinkedIn post created successfully")
                return response.json()
            else:
                logger.error(f"Failed to create LinkedIn post: {response.status_code} - {response.text}")
                return {"error": response.text, "status_code": response.status_code}

        except Exception as e:
            logger.error(f"Error creating LinkedIn post: {e}")
            return {"error": str(e)}

    def create_article_post(self, title: str, description: str, original_url: str,
                           visibility: str = "PUBLIC") -> Dict:
        """Create a LinkedIn post with an article link."""
        try:
            post_data = {
                "author": f"urn:li:person:{self._get_person_urn_id()}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": f"{title}\n\n{description}"
                        },
                        "shareMediaCategory": "ARTICLE",
                        "media": [
                            {
                                "status": "READY",
                                "description": {"text": description},
                                "originalUrl": original_url,
                                "title": {"text": title}
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }

            response = requests.post(
                f"{self.api_base_url}{self.business_updates_path}",
                headers=self.headers,
                json=post_data
            )

            if response.status_code == 201:
                logger.info("LinkedIn article post created successfully")
                return response.json()
            else:
                logger.error(f"Failed to create LinkedIn article post: {response.status_code} - {response.text}")
                return {"error": response.text, "status_code": response.status_code}

        except Exception as e:
            logger.error(f"Error creating LinkedIn article post: {e}")
            return {"error": str(e)}

    def _get_person_urn_id(self):
        """Get the person's URN ID from the access token."""
        # In a real implementation, you would use the /me endpoint to get the person ID
        # For this demo, we'll return a placeholder - this would need to be replaced with real API call
        return "PLACEHOLDER_PERSON_URN_ID"

    def get_my_profile(self):
        """Get the authenticated user's LinkedIn profile."""
        try:
            response = requests.get(
                f"{self.api_base_url}/me",
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get profile: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None

    def schedule_post(self, text: str, scheduled_time: datetime, visibility: str = "PUBLIC"):
        """Schedule a post for a future time."""
        # For now, we'll just log the scheduled post
        # In a real implementation, you would store this in a database and use a scheduler
        logger.info(f"Scheduled post for {scheduled_time}: {text}")
        return {
            "status": "scheduled",
            "text": text,
            "scheduled_time": scheduled_time.isoformat(),
            "visibility": visibility
        }

class LinkedInScheduler:
    """Handles scheduling of LinkedIn posts."""

    def __init__(self):
        self.posts_dir = Path("Scheduled_Posts")
        self.posts_dir.mkdir(exist_ok=True)

    def create_scheduled_post(self, text: str, scheduled_datetime: datetime,
                             title: str = "", description: str = "",
                             original_url: str = ""):
        """Create a scheduled LinkedIn post."""
        timestamp = scheduled_datetime.strftime("%Y%m%d_%H%M%S")
        post_filename = f"LINKEDIN_POST_{timestamp}.json"
        post_filepath = self.posts_dir / post_filename

        post_data = {
            "id": timestamp,
            "text": text,
            "title": title,
            "description": description,
            "original_url": original_url,
            "scheduled_time": scheduled_datetime.isoformat(),
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }

        post_filepath.write_text(json.dumps(post_data, indent=2))
        logger.info(f"Created scheduled post: {post_filepath.name}")
        return post_filepath

    def check_and_post(self):
        """Check for scheduled posts and post them if it's time."""
        # Look for scheduled posts
        scheduled_posts = list(self.posts_dir.glob("*.json"))
        now = datetime.now()

        posted_count = 0

        for post_file in scheduled_posts:
            try:
                with open(post_file, 'r') as f:
                    post_data = json.load(f)

                scheduled_time = datetime.fromisoformat(post_data['scheduled_time'])

                if now >= scheduled_time and post_data['status'] == 'scheduled':
                    # It's time to post
                    success = self.execute_post(post_data)

                    # Update status
                    post_data['status'] = 'posted' if success else 'failed'
                    post_data['executed_at'] = datetime.now().isoformat()

                    with open(post_file, 'w') as f:
                        json.dump(post_data, f, indent=2)

                    if success:
                        posted_count += 1
                        logger.info(f"Successfully posted scheduled update: {post_file.name}")
                    else:
                        logger.error(f"Failed to post scheduled update: {post_file.name}")

            except Exception as e:
                logger.error(f"Error processing scheduled post {post_file}: {e}")

        return posted_count

    def execute_post(self, post_data: dict):
        """Execute a LinkedIn post."""
        try:
            poster = LinkedInPoster()

            if post_data.get('original_url'):
                # Post with article link
                result = poster.create_article_post(
                    title=post_data.get('title', ''),
                    description=post_data.get('description', ''),
                    original_url=post_data['original_url']
                )
            else:
                # Regular text post
                result = poster.create_text_post(post_data['text'])

            return 'error' not in result

        except Exception as e:
            logger.error(f"Error executing post: {e}")
            return False

def main():
    """Main function to demonstrate LinkedIn posting."""
    try:
        # Example: Create a sample LinkedIn post
        poster = LinkedInPoster()

        sample_post = """
        Exciting updates from our team! We've been working hard to deliver exceptional results for our clients.

        Our AI Employee system is now operational with Bronze Tier features and we're moving into Silver Tier development with automated LinkedIn posting capabilities!

        #AI #Automation #BusinessGrowth #Innovation
        """

        print("This would post to LinkedIn if proper API credentials were provided:")
        print("Post content:", sample_post)

        # In a real implementation, you would call:
        # result = poster.create_text_post(sample_post)
        # print("Post result:", result)

        # Example: Schedule a post
        scheduler = LinkedInScheduler()
        future_time = datetime.now().replace(hour=14, minute=30, second=0, microsecond=0)  # Today at 2:30 PM

        scheduler.create_scheduled_post(
            text="Today's business tip: Automation can save you hours each week!",
            scheduled_datetime=future_time,
            title="Daily Business Tip",
            description="Learn how automation can improve your business efficiency"
        )

    except Exception as e:
        logger.error(f"Error in LinkedIn poster demo: {e}")

if __name__ == "__main__":
    main()