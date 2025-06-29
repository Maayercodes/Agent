from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from instagram_private_api import Client, ClientError
from typing import List, Dict, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
from loguru import logger
from ..database.models import Influencer, Platform

load_dotenv()

class InfluencerScraper:
    def __init__(self, session):
        self.session = session
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
        
        # Instagram credentials would go here in a production environment
        # self.instagram_username = os.getenv('INSTAGRAM_USERNAME')
        # self.instagram_password = os.getenv('INSTAGRAM_PASSWORD')
        # self.instagram_api = Client(self.instagram_username, self.instagram_password)

    def search_youtube_channels(self, keywords: List[str], max_results: int = 50) -> List[Dict]:
        """Search for YouTube channels based on keywords."""
        logger.info(f"Searching YouTube channels for keywords: {keywords}")
        channels = []

        try:
            for keyword in keywords:
                search_response = self.youtube.search().list(
                    q=keyword,
                    type='channel',
                    part='id,snippet',
                    maxResults=max_results
                ).execute()

                for item in search_response.get('items', []):
                    channel_id = item['id']['channelId']
                    
                    # Get detailed channel information
                    channel_response = self.youtube.channels().list(
                        part='snippet,statistics',
                        id=channel_id
                    ).execute()

                    if channel_response['items']:
                        channel_info = channel_response['items'][0]
                        subscriber_count = int(channel_info['statistics']['subscriberCount'])
                        
                        # Only include channels with significant following
                        if subscriber_count >= 1000:
                            channel = {
                                'name': channel_info['snippet']['title'],
                                'platform': Platform.YOUTUBE,
                                'follower_count': subscriber_count,
                                'country': channel_info['snippet'].get('country', ''),
                                'bio': channel_info['snippet']['description'],
                                'contact_page': f"https://www.youtube.com/channel/{channel_id}/about",
                                'niche': keyword,
                                'engagement_rate': float(channel_info['statistics']['viewCount']) / subscriber_count
                            }
                            channels.append(channel)

        except HttpError as e:
            logger.error(f"Error searching YouTube channels: {str(e)}")

        return channels

    def extract_email_from_description(self, text: str) -> Optional[str]:
        """Extract email address from text using regex."""
        import re
        email_pattern = r'[\w\.-]+@[\w\.-]+\.[\w]{2,}'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None

    def get_youtube_channel_email(self, channel_id: str) -> Optional[str]:
        """Attempt to find email address from channel about page."""
        try:
            channel_response = self.youtube.channels().list(
                part='snippet',
                id=channel_id
            ).execute()

            if channel_response['items']:
                description = channel_response['items'][0]['snippet']['description']
                return self.extract_email_from_description(description)

        except HttpError as e:
            logger.error(f"Error getting channel email: {str(e)}")

        return None

    def search_instagram_influencers(self, keywords: List[str], min_followers: int = 10000) -> List[Dict]:
        """Search for Instagram influencers based on keywords.
        Note: This is a placeholder. Real implementation would require Instagram API access.
        """
        logger.info(f"Searching Instagram influencers for keywords: {keywords}")
        influencers = []

        # Placeholder for Instagram scraping logic
        # In a production environment, you would:
        # 1. Use Instagram's Graph API with proper authentication
        # 2. Or use a third-party influencer platform API
        # 3. Or implement careful scraping with proper rate limiting

        return influencers

    def save_to_db(self, influencers: List[Dict]) -> None:
        """Save influencer data to database."""
        try:
            for influencer_data in influencers:
                # Check if influencer already exists
                existing = self.session.query(Influencer).filter_by(
                    name=influencer_data['name'],
                    platform=influencer_data['platform']
                ).first()

                if existing:
                    # Update existing record
                    for key, value in influencer_data.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    influencer = Influencer(**influencer_data)
                    self.session.add(influencer)

            self.session.commit()
            logger.success(f"Successfully saved {len(influencers)} influencers to database")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving to database: {str(e)}")

    def scrape_all(self, keywords: List[str]) -> None:
        """Scrape influencers from all platforms for given keywords."""
        # YouTube scraping
        youtube_influencers = self.search_youtube_channels(keywords)
        if youtube_influencers:
            self.save_to_db(youtube_influencers)

        # Instagram scraping
        instagram_influencers = self.search_instagram_influencers(keywords)
        if instagram_influencers:
            self.save_to_db(instagram_influencers)

if __name__ == '__main__':
    # Example usage
    from ..database.models import init_db
    
    session = init_db()
    scraper = InfluencerScraper(session)
    
    keywords = [
        'parenting tips',
        'early childhood education',
        'kids activities',
        'mommy vlogger',
        'educational toys'
    ]
    
    scraper.scrape_all(keywords)