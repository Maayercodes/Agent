# AI-Powered Marketing Outreach Platform

An automated marketing outreach system for children's storytelling platform targeting daycares and influencers in the USA and France.

## 🌟 Features

### Data Collection
- Automated scraping of daycare data from multiple sources (Yelp, Care.com, Yellowpages, nounou-top.fr, assistantes-maternelles.fr)
- Influencer data collection from YouTube and Instagram
- Structured data storage in PostgreSQL/SQLite database

### AI Assistant
- Natural language command processing
- Intelligent data filtering and querying
- GPT-powered personalized content generation

### Outreach Automation
- Automated email campaigns in English and French
- Email tracking (sent, bounce, open, reply)
- Template-based personalization

### User Interface
- Streamlit web dashboard
- Command-line interface
- Real-time analytics

## 🚀 Setup

1. Clone the repository
```bash
git clone [repository-url]
cd marketing-outreach
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your API keys and credentials
```

5. Initialize database
```bash
python src/database/init_db.py
```

## 📁 Project Structure

```
├── src/
│   ├── scrapers/         # Data collection modules
│   ├── database/         # Database models and operations
│   ├── ai_assistant/     # GPT-based assistant logic
│   ├── outreach/         # Email automation
│   ├── templates/        # Email templates
│   └── ui/              # Web interface and CLI
├── tests/               # Unit and integration tests
├── data/               # Scraped data storage
├── logs/               # Application logs
├── requirements.txt    # Project dependencies
└── .env               # Configuration variables
```

## 🔧 Configuration

Required environment variables:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# OpenAI
OPENAI_API_KEY=your_key_here

# Email
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_specific_password

# APIs
YOUTUBE_API_KEY=your_key_here
DEEPL_API_KEY=your_key_here
```

## 🎯 Usage

### Web Dashboard
```bash
python src/ui/app.py
```

### CLI Interface
```bash
python src/ui/cli.py --help
```

Example commands:
```bash
# Scrape data
python src/ui/cli.py scrape --source yelp --region usa

# Query data
python src/ui/cli.py query "Find influencers in France with 10k+ followers"

# Send outreach
python src/ui/cli.py outreach --target daycare --count 50 --region usa
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.