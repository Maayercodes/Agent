from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from loguru import logger
from ..database.models import Daycare, Influencer, Region, Platform
from ..outreach.email_sender import EmailSender
import asyncio

load_dotenv()

class AIAssistant:
    def __init__(self, session: Session):
        self.session = session
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-3.5-turbo"
        self.client = AsyncOpenAI(api_key=self.openai_api_key)
        self.email_sender = EmailSender(session)

    async def process_command(self, command: str) -> Dict[str, Any]:
        """Main entry point for commands"""
        try:
            intent = await self._analyze_intent(command)
            
            if intent['action'] == 'search_influencers':
                return await self._handle_influencer_search(intent['params'])
            elif intent['action'] == 'search_daycares':
                return await self._handle_daycare_search(intent['params'])
            elif intent['action'] == 'send_outreach':
                return await self._handle_outreach(intent['params'])
            else:
                return {"error": "Unsupported command"}
        except Exception as e:
            logger.error(f"Command processing failed: {str(e)}")
            return {"error": str(e)}

    async def _analyze_intent(self, command: str) -> Dict[str, Any]:
        """Analyze user command using GPT"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Analyze this marketing command and return JSON with:
                        - "action": "search_influencers", "search_daycares", or "send_outreach"
                        - "params": {relevant parameters}"""
                    },
                    {"role": "user", "content": command}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Intent analysis failed: {str(e)}")
            raise

    async def _handle_influencer_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search influencers in database"""
        query = self.session.query(Influencer)
        if 'country' in params:
            query = query.filter(Influencer.country == params['country'])
        if 'min_followers' in params:
            query = query.filter(Influencer.follower_count >= params['min_followers'])
        
        influencers = query.all()
        return {
            "influencers": [{
                "name": inf.name,
                "platform": inf.platform.value,
                "followers": inf.follower_count,
                "country": inf.country
            } for inf in influencers]
        }

    async def _handle_daycare_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search daycares in database"""
        query = self.session.query(Daycare)
        if 'city' in params:
            query = query.filter(func.lower(Daycare.city) == params['city'].lower())
        if 'limit' in params:
            query = query.limit(params['limit'])
        
        daycares = query.all()
        return {
            "daycares": [{
                "name": dc.name,
                "city": dc.city,
                "region": dc.region.value
            } for dc in daycares]
        }

    async def _handle_outreach(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle outreach campaign commands."""
        try:
            if params['target_type'] == 'daycare':
                targets = self.session.query(Daycare)\
                    .filter(Daycare.last_contacted == None)\
                    .filter(Daycare.region == params['region'])\
                    .order_by(func.random())\
                    .limit(params['count'])\
                    .all()
            else:
                targets = self.session.query(Influencer)\
                    .filter(Influencer.last_contacted == None)\
                    .order_by(func.random())\
                    .limit(params['count'])\
                    .all()

            results = await self.email_sender.send_batch(targets, params['target_type'])
            
            return {
                "success": True,
                "messages_sent": len(results),
                "details": results
            }
        except Exception as e:
            logger.error(f"Error in outreach campaign: {str(e)}")
            return {"error": str(e)}

if __name__ == '__main__':
    from ..database.models import init_db
    
    async def main():
        session = init_db()
        assistant = AIAssistant(session)
        
        commands = [
            "Find all influencers in France with 10k+ followers",
            "List top 10 daycares in New York",
            "Send outreach email to 50 random USA daycares"
        ]
        
        for command in commands:
            try:
                result = await assistant.process_command(command)
                print(f"Command: {command}")
                print(f"Result: {result}\n")
            except Exception as e:
                print(f"Error processing '{command}': {str(e)}")

    # Proper event loop handling
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "Event loop is closed" not in str(e):
            raise