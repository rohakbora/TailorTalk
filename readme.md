# TailorTalk 📅

**TailorTalk** is an AI-powered calendar assistant that helps you manage your Google Calendar through natural language conversations. Built with FastAPI, Streamlit, and powered by LangGraph for intelligent workflow management.

## 🌟 Features

- **Natural Language Calendar Management**: Interact with your calendar using everyday language
- **Real-time Calendar Operations**: Check availability, book meetings, and list events
- **Smart Time Parsing**: Understands "tomorrow", "next Monday", "in 3 days", etc.
- **Overlap Detection**: Prevents double-booking with intelligent conflict detection
- **Multi-API Key Support**: Load balancing across multiple OpenRouter API keys
- **Session Management**: Maintains conversation context across interactions
- **Live Calendar View**: Integrated calendar interface for visual management

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │ Google Calendar │
│   Frontend      │────│   Backend       │────│      API        │
│   (app.py)      │    │   (main.py)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   LangGraph     │
                    │  Agent System   │
                    │(message_graph.py)│
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Calendar API credentials
- OpenRouter API key(s)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tailortalk
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   # OpenRouter API Keys (comma-separated for load balancing)
   OPENROUTER_API_KEY=your_key
   
   # Google Calendar API Credentials
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GOOGLE_REFRESH_TOKEN=your_refresh_token
   TAILORTALK_CALENDAR_ID=your_calendar_id
   ```

4. **Start the backend server**
   ```bash
   python main.py
   ```
   Server will start on `http://localhost:8000`

5. **Launch the frontend**
   ```bash
   streamlit run app.py
   ```
   Open `http://localhost:8501` in your browser

## 📋 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Main conversation endpoint |
| `/health` | GET | Health check and system status |
| `/sessions` | GET | View active user sessions |
| `/sessions/{user_id}` | DELETE | Clear specific user session |
| `/sessions` | DELETE | Clear all sessions |

### Test Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/test-calendar` | GET | Test Google Calendar connectivity |
| `/test-llm` | GET | Test OpenRouter/LLM connectivity |

## 🛠️ Usage Examples

### Basic Commands

**Check Availability:**
```
"Check my availability tomorrow"
"Am I free next Monday from 2-4 PM?"
"What's my schedule this week?"
```

**Book Meetings:**
```
"Book a meeting tomorrow at 2 PM for 1 hour"
"Schedule a team sync on 2025-06-30 at 14:00 for 2 hours"
"Set up a client call next Friday at 3 PM"
```

**List Events:**
```
"What's on my calendar today?"
"Show my upcoming meetings"
"List events for next week"
```

### API Usage

```python
import requests

# Send a chat message
response = requests.post("http://localhost:8000/chat", json={
    "message": "Check my availability tomorrow",
    "user_id": "optional_user_id"
})

result = response.json()
print(result["response"])
```

## 🔧 Configuration

### Calendar Tools

The system includes three main calendar operations:

1. **`check_availability`** - Check free/busy times in date ranges
2. **`book_slot`** - Create new calendar events with conflict detection
3. **`list_events`** - Retrieve and format upcoming events

### Time Zone Handling

- Default timezone: `Asia/Kolkata` (IST)
- Automatic UTC conversion for Google Calendar API
- Natural language time parsing with context awareness

### LLM Configuration

- Model: `deepseek/deepseek-chat-v3-0324:free` (configurable)
- Temperature: 0.3 for consistent responses
- Automatic fallback between multiple API keys

## 📁 Project Structure

```
tailortalk/
├── app/
│   ├── calender_utils.py    # Google Calendar API utilities
│   ├── memory.py            # Session state management
│   └── tools.py             # Calendar operation tools
├── agent/
│   └── message_graph.py     # LangGraph workflow definition
├── main.py                  # FastAPI application
├── app.py                   # Streamlit frontend
├── requirements.txt         # Python dependencies
└── .env                     # Environment configuration
```

## 🔒 Security & Authentication

### Google Calendar Setup

1. Create a project in Google Cloud Console
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Generate refresh token using the OAuth flow
5. Add credentials to `.env` file

### API Key Management

- Supports multiple OpenRouter API keys for load balancing
- Keys are rotated randomly for each request
- Secure environment variable storage

## 🐛 Troubleshooting

### Common Issues

**Calendar Connection Failed:**
- Verify Google API credentials in `.env`
- Check calendar ID permissions
- Ensure refresh token is valid

**LLM Connection Failed:**
- Verify OpenRouter API keys
- Check network connectivity
- Monitor API rate limits

**Tool Execution Errors:**
- Check date format parsing
- Verify timezone configuration
- Review calendar permissions

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LangGraph** - For intelligent agent workflow management
- **OpenRouter** - For LLM API access
- **Google Calendar API** - For calendar integration
- **FastAPI** - For robust backend framework
- **Streamlit** - For rapid frontend development

---

**Built with ❤️ for seamless calendar management through AI**
