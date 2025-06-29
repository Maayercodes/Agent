import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Union, Any
from datetime import datetime
import os
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from ..database.models import Daycare, Influencer, OutreachHistory

load_dotenv()

class EmailSender:
    def __init__(self, session):
        self.session = session
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.sender_email = os.getenv('GMAIL_USER')
        self.sender_name = os.getenv('EMAIL_SENDER_NAME')
        self.password = os.getenv('GMAIL_APP_PASSWORD')
        
        # Initialize Jinja2 environment
        self.template_env = Environment(
            loader=FileSystemLoader('src/templates/emails')
        )

    async def send_batch(self, targets: List[Union[Daycare, Influencer]], target_type: str) -> List[Dict[str, Any]]:
        """Send batch emails to multiple targets."""
        results = []
        
        for target in targets:
            try:
                # Determine language based on region
                language = 'fr' if getattr(target, 'region', None) == 'FRANCE' else 'en'
                
                # Generate email content
                subject, body = self._generate_email_content(target, target_type, language)
                
                # Send email
                success = await self._send_email(target.email, subject, body)
                
                if success:
                    # Update database
                    self._record_outreach(target, target_type, subject, body, language)
                    results.append({
                        "target": target.name,
                        "email": target.email,
                        "status": "success"
                    })
                else:
                    results.append({
                        "target": target.name,
                        "email": target.email,
                        "status": "failed"
                    })
                    
            except Exception as e:
                logger.error(f"Error sending email to {target.name}: {str(e)}")
                results.append({
                    "target": target.name,
                    "email": target.email,
                    "status": "error",
                    "error": str(e)
                })
                
        return results

    def _generate_email_content(self, target: Union[Daycare, Influencer], target_type: str, language: str) -> tuple:
        """Generate personalized email content using templates."""
        template_name = f"{target_type}_{language}.html"
        template = self.template_env.get_template(template_name)
        
        # Common template variables
        context = {
            "recipient_name": target.name,
            "sender_name": self.sender_name
        }
        
        # Add target-specific variables
        if target_type == 'daycare':
            context.update({
                "city": target.city,
                "region": target.region.value
            })
        else:  # influencer
            context.update({
                "platform": target.platform.value,
                "niche": target.niche
            })
        
        # Get subject line template
        subject_template = self.template_env.get_template(f"subject_{target_type}_{language}.txt")
        
        subject = subject_template.render(context)
        body = template.render(context)
        
        return subject, body

    async def _send_email(self, recipient_email: str, subject: str, body: str) -> bool:
        """Send an email using SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = recipient_email

            # Add HTML content
            msg.attach(MIMEText(body, 'html'))

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.send_message(msg)

            return True

        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {str(e)}")
            return False

    def _record_outreach(self, target: Union[Daycare, Influencer], target_type: str,
                        subject: str, content: str, language: str) -> None:
        """Record outreach attempt in database."""
        try:
            # Create outreach history record
            history = OutreachHistory(
                target_type=target_type,
                target_id=target.id,
                email_subject=subject,
                email_content=content,
                language=language
            )
            self.session.add(history)
            
            # Update target's last_contacted timestamp
            target.last_contacted = datetime.utcnow()
            
            self.session.commit()
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording outreach: {str(e)}")

if __name__ == '__main__':
    # Example usage
    from ..database.models import init_db
    import asyncio
    
    async def main():
        session = init_db()
        sender = EmailSender(session)
        
        # Get some test targets
        daycares = session.query(Daycare).limit(5).all()
        
        # Send test emails
        results = await sender.send_batch(daycares, 'daycare')
        print("Email sending results:", results)
    
    asyncio.run(main())