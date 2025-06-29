import streamlit as st
import asyncio
import pandas as pd
from datetime import datetime
from typing import List, Dict
import os
from dotenv import load_dotenv
from ..database.models import init_db, Daycare, Influencer, Region, Platform
from ..ai_assistant.assistant import AIAssistant
from ..scrapers.daycare_scraper import DaycareScraper
from ..scrapers.influencer_scraper import InfluencerScraper

load_dotenv()

# Initialize session state
if 'assistant' not in st.session_state:
    session = init_db()
    st.session_state.assistant = AIAssistant(session)
    st.session_state.daycare_scraper = DaycareScraper(session)
    st.session_state.influencer_scraper = InfluencerScraper(session)

def main():
    st.set_page_config(page_title="AI Marketing Outreach Platform", layout="wide")
    
    st.title("🤖 AI Marketing Outreach Platform")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "Data Collection", "AI Assistant", "Outreach Campaigns", "Analytics"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Data Collection":
        show_data_collection()
    elif page == "AI Assistant":
        show_ai_assistant()
    elif page == "Outreach Campaigns":
        show_outreach_campaigns()
    elif page == "Analytics":
        show_analytics()

def show_dashboard():
    st.header("📊 Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Daycares", len(st.session_state.assistant.session.query(Daycare).all()))
    
    with col2:
        st.metric("Total Influencers", len(st.session_state.assistant.session.query(Influencer).all()))
    
    with col3:
        total_emails = st.session_state.assistant.session.query(Daycare).filter(Daycare.last_contacted.isnot(None)).count() + \
                      st.session_state.assistant.session.query(Influencer).filter(Influencer.last_contacted.isnot(None)).count()
        st.metric("Emails Sent", total_emails)

def show_data_collection():
    st.header("🔍 Data Collection")
    
    tab1, tab2 = st.tabs(["Daycare Scraping", "Influencer Scraping"])
    
    with tab1:
        st.subheader("Daycare Data Collection")
        
        col1, col2 = st.columns(2)
        with col1:
            country = st.selectbox("Select Country", ["USA", "FRANCE"])
        
        with col2:
            if country == "USA":
                city = st.text_input("Enter City")
                state = st.text_input("Enter State (e.g., NY)")
            else:
                city = st.text_input("Enter City")
                state = None
        
        if st.button("Start Daycare Scraping"):
            with st.spinner("Scraping daycare data..."):
                cities = [{'city': city, 'state': state, 'country': country}]
                st.session_state.daycare_scraper.scrape_all(cities)
                st.success("Scraping completed!")
    
    with tab2:
        st.subheader("Influencer Data Collection")
        
        keywords = st.text_area(
            "Enter keywords (one per line)",
            "parenting tips\nearly childhood education\nkids activities"
        ).split('\n')
        
        if st.button("Start Influencer Scraping"):
            with st.spinner("Scraping influencer data..."):
                st.session_state.influencer_scraper.scrape_all(keywords)
                st.success("Scraping completed!")

def show_ai_assistant():
    st.header("🧠 AI Assistant")
    
    user_input = st.text_input(
        "Enter your command",
        placeholder="e.g., 'Find all influencers in France with 10k+ followers'"
    )
    
    if user_input:
        with st.spinner("Processing your request..."):
            result = asyncio.run(st.session_state.assistant.process_command(user_input))
            
            if 'error' in result:
                st.error(result['error'])
            else:
                if 'influencers' in result:
                    st.dataframe(pd.DataFrame(result['influencers']))
                elif 'daycares' in result:
                    st.dataframe(pd.DataFrame(result['daycares']))
                elif 'success' in result:
                    st.success(f"Successfully sent {result['messages_sent']} messages!")

def show_outreach_campaigns():
    st.header("📤 Outreach Campaigns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        target_type = st.selectbox("Select Target Type", ["daycare", "influencer"])
        count = st.number_input("Number of Recipients", min_value=1, max_value=100, value=10)
    
    with col2:
        if target_type == "daycare":
            region = st.selectbox("Select Region", ["USA", "FRANCE"])
        else:
            region = None
    
    if st.button("Start Campaign"):
        with st.spinner("Sending emails..."):
            command = f"Send outreach email to {count} random {region if region else ''} {target_type}s"
            result = asyncio.run(st.session_state.assistant.process_command(command))
            
            if 'error' in result:
                st.error(result['error'])
            else:
                st.success(f"Campaign completed! Sent {result['messages_sent']} emails.")
                st.json(result['details'])

def show_analytics():
    st.header("📈 Analytics")
    
    # Email statistics
    st.subheader("Email Campaign Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sent = st.session_state.assistant.session.query(Daycare).filter(Daycare.last_contacted.isnot(None)).count() + \
                     st.session_state.assistant.session.query(Influencer).filter(Influencer.last_contacted.isnot(None)).count()
        st.metric("Total Emails Sent", total_sent)
    
    with col2:
        total_opened = st.session_state.assistant.session.query(Daycare).filter(Daycare.email_opened == True).count() + \
                      st.session_state.assistant.session.query(Influencer).filter(Influencer.email_opened == True).count()
        st.metric("Emails Opened", total_opened)
    
    with col3:
        total_replied = st.session_state.assistant.session.query(Daycare).filter(Daycare.email_replied == True).count() + \
                       st.session_state.assistant.session.query(Influencer).filter(Influencer.email_replied == True).count()
        st.metric("Replies Received", total_replied)
    
    with col4:
        if total_sent > 0:
            response_rate = (total_replied / total_sent) * 100
            st.metric("Response Rate", f"{response_rate:.1f}%")

if __name__ == "__main__":
    main()