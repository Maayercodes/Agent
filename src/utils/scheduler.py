from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from loguru import logger
from typing import List, Dict
from ..database.models import init_db, Daycare, Influencer
from ..scrapers.daycare_scraper import DaycareScraper
from ..scrapers.influencer_scraper import InfluencerScraper

load_dotenv()

class TaskScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.session = init_db()
        self.daycare_scraper = DaycareScraper(self.session)
        self.influencer_scraper = InfluencerScraper(self.session)

    def start(self):
        """Start the scheduler."""
        if os.getenv('ENABLE_SCHEDULED_SCRAPING', 'true').lower() == 'true':
            # Schedule weekly scraping tasks
            self.scheduler.add_job(
                self.run_daycare_scraping,
                CronTrigger(day_of_week='mon', hour=1),  # Run every Monday at 1 AM
                name='daycare_scraping'
            )
            
            self.scheduler.add_job(
                self.run_influencer_scraping,
                CronTrigger(day_of_week='tue', hour=1),  # Run every Tuesday at 1 AM
                name='influencer_scraping'
            )
            
            # Schedule daily email tracking update
            self.scheduler.add_job(
                self.update_email_tracking,
                CronTrigger(hour=*/4),  # Run every 4 hours
                name='email_tracking'
            )
            
            # Schedule database cleanup
            self.scheduler.add_job(
                self.cleanup_old_records,
                CronTrigger(day=1),  # Run on the first day of each month
                name='database_cleanup'
            )
        
        self.scheduler.start()
        logger.info("Scheduler started successfully")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

    def run_daycare_scraping(self):
        """Run scheduled daycare scraping."""
        try:
            cities = [
                {'city': 'New York', 'state': 'NY', 'country': 'USA'},
                {'city': 'Los Angeles', 'state': 'CA', 'country': 'USA'},
                {'city': 'Paris', 'state': None, 'country': 'FRANCE'},
                {'city': 'Lyon', 'state': None, 'country': 'FRANCE'}
            ]
            
            self.daycare_scraper.scrape_all(cities)
            logger.success("Scheduled daycare scraping completed successfully")
            
        except Exception as e:
            logger.error(f"Scheduled daycare scraping failed: {str(e)}")

    def run_influencer_scraping(self):
        """Run scheduled influencer scraping."""
        try:
            keywords = [
                'parenting tips',
                'early childhood education',
                'kids activities',
                'mommy vlogger',
                'educational toys'
            ]
            
            self.influencer_scraper.scrape_all(keywords)
            logger.success("Scheduled influencer scraping completed successfully")
            
        except Exception as e:
            logger.error(f"Scheduled influencer scraping failed: {str(e)}")

    def update_email_tracking(self):
        """Update email tracking status."""
        try:
            # This is a placeholder for email tracking implementation
            # In a real application, you would:
            # 1. Check email open tracking pixels
            # 2. Check for email replies
            # 3. Update database accordingly
            
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Update daycare tracking
            daycares = self.session.query(Daycare)\
                .filter(Daycare.last_contacted >= cutoff_date)\
                .filter(Daycare.email_opened == False)\
                .all()
            
            for daycare in daycares:
                # Implement email tracking check logic here
                pass
            
            # Update influencer tracking
            influencers = self.session.query(Influencer)\
                .filter(Influencer.last_contacted >= cutoff_date)\
                .filter(Influencer.email_opened == False)\
                .all()
            
            for influencer in influencers:
                # Implement email tracking check logic here
                pass
            
            self.session.commit()
            logger.success("Email tracking update completed successfully")
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Email tracking update failed: {str(e)}")

    def cleanup_old_records(self):
        """Clean up old records from the database."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=180)  # 6 months
            
            # Delete old records
            self.session.query(Daycare)\
                .filter(Daycare.updated_at < cutoff_date)\
                .filter(Daycare.email_replied == False)\
                .delete()
            
            self.session.query(Influencer)\
                .filter(Influencer.updated_at < cutoff_date)\
                .filter(Influencer.email_replied == False)\
                .delete()
            
            self.session.commit()
            logger.success("Database cleanup completed successfully")
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Database cleanup failed: {str(e)}")

if __name__ == '__main__':
    scheduler = TaskScheduler()
    try:
        scheduler.start()
        # Keep the script running
        try:
            while True:
                pass
        except KeyboardInterrupt:
            scheduler.stop()
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")
        scheduler.stop()