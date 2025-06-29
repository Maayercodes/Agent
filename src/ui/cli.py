import click
import asyncio
import json
from typing import List, Dict
import os
from dotenv import load_dotenv
from database.models import init_db, Daycare, Influencer, Region
from ..ai_assistant.assistant import AIAssistant
from ..scrapers.daycare_scraper import DaycareScraper
from ..scrapers.influencer_scraper import InfluencerScraper

load_dotenv()

@click.group()
def cli():
    """AI Marketing Outreach Platform CLI"""
    pass

async def run_async_command(func, *args, **kwargs):
    """Helper to run async commands with proper event loop handling"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        return {"error": str(e)}

@cli.command()
@click.option('--source', type=click.Choice(['google_maps', 'care', 'nounou']), 
              help='Source to scrape from')
@click.option('--region', type=click.Choice(['usa', 'france']), 
              help='Region to target')
@click.option('--city', required=True, help='City to scrape')
@click.option('--state', help='State (for USA only)')
@click.option('--query', default="day care centers", 
              help='Search query for Google Maps')
@click.option('--max-results', default=20, 
              help='Maximum results to fetch')
@click.option('--headless/--no-headless', default=True,
              help='Run browser in headless mode')
def scrape(source: str, region: str, city: str, state: str = None, 
          query: str = "day care centers", max_results: int = 20,
          headless: bool = True):
    """Scrape daycare data from specified source."""
    session = init_db()
    scraper = DaycareScraper(session, headless=headless)
    
    if source == 'google_maps':
        click.echo(f"Starting Google Maps scraping for {query} in {city}, {region.upper()}...")
        results = scraper.scrape_google_maps(
            query=query,
            city=city,
            max_results=max_results
        )
        
        if not results:
            click.echo("No results found!", err=True)
            return
            
        saved_count = scraper.save_to_db(results, region=region)
        click.echo(f"Successfully saved {saved_count} daycares to database")
    else:
        cities = [{
            'city': city,
            'state': state,
            'country': region.upper()
        }]
        scraper.scrape_all(cities)
    
    click.echo("Scraping completed!")

@cli.command()
@click.option('--platform', type=click.Choice(['youtube', 'instagram']), 
              help='Platform to scrape')
@click.option('--keywords', help='Keywords to search for (comma-separated)')
@click.option('--min-followers', type=int, default=1000, 
              help='Minimum follower count')
def scrape_influencers(platform: str, keywords: str, min_followers: int):
    """Scrape influencer data from specified platform."""
    session = init_db()
    scraper = InfluencerScraper(session)
    
    keyword_list = [k.strip() for k in keywords.split(',')]
    click.echo(f"Starting influencer scraping from {platform}...")
    scraper.scrape_all(keyword_list)
    click.echo("Scraping completed!")

@cli.command()
@click.argument('query')
def query(query: str):
    """Process a natural language query using the AI assistant."""
    async def process_query():
        session = init_db()
        assistant = AIAssistant(session)
        try:
            click.echo("Processing query...")
            result = await assistant.process_command(query)
            if 'error' in result:
                click.echo(f"Error: {result['error']}", err=True)
            else:
                click.echo(json.dumps(result, indent=2))
        finally:
            session.close()
    
    # Windows-compatible async handling
    try:
        asyncio.run(process_query())
    except RuntimeError as e:
        if "Event loop is closed" not in str(e):
            raise

@cli.command()
@click.option('--target', type=click.Choice(['daycare', 'influencer']), 
              required=True, help='Target type')
@click.option('--count', type=int, required=True, help='Number of targets')
@click.option('--region', type=click.Choice(['USA', 'FRANCE']), 
              help='Region (for daycares only)')
def outreach(target: str, count: int, region: str = None):
    """Send outreach emails to specified targets."""
    async def run_outreach():
        session = init_db()
        assistant = AIAssistant(session)
        try:
            command = f"Send outreach email to {count} random {region + ' ' if region else ''}{target}s"
            click.echo(f"Starting outreach campaign...")
            result = await assistant.process_command(command)
            
            if 'error' in result:
                click.echo(f"Error: {result['error']}", err=True)
            else:
                click.echo(f"Successfully sent {result['messages_sent']} emails!")
                click.echo("Details:")
                click.echo(json.dumps(result['details'], indent=2))
        finally:
            session.close()
    
    try:
        asyncio.run(run_outreach())
    except RuntimeError as e:
        if "Event loop is closed" not in str(e):
            raise

@cli.command()
def stats():
    """Show platform statistics."""
    session = init_db()
    try:
        # Get daycare stats
        daycare_total = session.query(Daycare).count()
        daycare_contacted = session.query(Daycare).filter(Daycare.last_contacted.isnot(None)).count()
        daycare_replied = session.query(Daycare).filter(Daycare.email_replied == True).count()
        
        # Get influencer stats
        influencer_total = session.query(Influencer).count()
        influencer_contacted = session.query(Influencer).filter(Influencer.last_contacted.isnot(None)).count()
        influencer_replied = session.query(Influencer).filter(Influencer.email_replied == True).count()
        
        click.echo("\nPlatform Statistics:")
        click.echo("-" * 20)
        click.echo(f"Daycares:")
        click.echo(f"  Total: {daycare_total}")
        click.echo(f"  Contacted: {daycare_contacted}")
        click.echo(f"  Replied: {daycare_replied}")
        click.echo(f"\nInfluencers:")
        click.echo(f"  Total: {influencer_total}")
        click.echo(f"  Contacted: {influencer_contacted}")
        click.echo(f"  Replied: {influencer_replied}")
        
        total_sent = daycare_contacted + influencer_contacted
        total_replied = daycare_replied + influencer_replied
        if total_sent > 0:
            response_rate = (total_replied / total_sent) * 100
            click.echo(f"\nOverall Response Rate: {response_rate:.1f}%")
    finally:
        session.close()

if __name__ == '__main__':
    cli()