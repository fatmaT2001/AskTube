# AskTube

> **AI-Powered YouTube Video Learning Assistant**

AskTube transforms YouTube videos into interactive learning experiences through intelligent conversation. Built with enterprise-grade retrieval-augmented generation (RAG), it enables users to ask questions about video content and receive contextually accurate responses powered by state-of-the-art language models.

![AskTube Demo](screenshots/demo.gif)
*Interactive chat with YouTube video content*

## Key Features

- **Intelligent Video Processing**: Automatically extracts and indexes YouTube video transcripts
- **Semantic Search**: Advanced vector-based search through video content using Pinecone
- **Multi-Provider LLM Support**: Seamlessly switch between OpenAI, Groq, OpenRouter, and other providers
- **Real-time Chat Interface**: Interactive conversations with video content
- **Persistent Storage**: PostgreSQL-backed data persistence for videos, chats, and message history
- **Browser Extension**: Chrome extension for seamless YouTube integration

## Screenshots

### Chrome Extension Interface
![Chrome Extension](screenshots/chrome-extension.png)
*YouTube integration with AskTube sidepanel*

### Chat Interface
![Chat Interface](screenshots/chat-interface.png)
*Real-time conversation with video content*

### Video Management
![Video Management](screenshots/video-management.png)
*Manage and track video processing status*

## Architecture

AskTube follows a microservices architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Browser Ext.   │ ←→ │   FastAPI       │ ←→ │   PostgreSQL    │
│                 │    │   Backend       │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         
                              ▼                         
                       ┌─────────────────┐    ┌─────────────────┐
                       │    LiteLLM      │ ←→ │    Pinecone     │
                       │    Proxy        │    │   Vector DB     │
                       └─────────────────┘    └─────────────────┘
```

### Core Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **PostgreSQL** | Primary database for storing videos, chats, messages, and user data | PostgreSQL 13+ |
| **Pinecone** | Vector database for semantic search and RAG retrieval | Pinecone Cloud |
| **LiteLLM** | Universal LLM proxy enabling multi-provider model access | LiteLLM Proxy Server |
| **FastAPI** | High-performance API backend with async support | Python 3.11+ |
| **Chrome Extension** | Frontend interface integrated with YouTube | Vanilla JS |

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database (Supabase recommended)
- Pinecone account
- API keys for at least one LLM provider (OpenAI, Groq, or OpenRouter)

### Installation

1. **Clone and Setup Environment**
   ```bash
   git clone https://github.com/fatmaT2001/AskTube.git
   cd AskTube/server
   python -m venv env
   source env/bin/activate  # Linux/Mac
   # OR
   env\Scripts\activate     # Windows
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Configuration**
   
   The application uses SQLAlchemy and automatically creates all required database tables when FastAPI starts. 
   
   **For Supabase users:**
   - Use the Session Pooler connection (required for IPv4-only environments)
   - Configure your PostgreSQL connection string in `.env`
   
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase Session Pooler connection string
   ```

4. **Configure LiteLLM with Load Balancing**
   
   The current configuration includes intelligent load balancing:
   - **Video Summary Generation**: Map-reduce approach for handling large transcripts
   - **Answer Generation**: Load balancing across multiple model providers
   
   **Important:** Set your API keys as environment variables before starting LiteLLM:
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export GROQ_API_KEY="your-groq-key"
   export OPENROUTER_API_KEY="your-openrouter-key"
   ```
   
   For load balancing, use the same model name for groups of models in `litellm_config.yaml`.

5. **Start Services**
   ```bash
   # Terminal 1: Start LiteLLM Proxy
   litellm --host 127.0.0.1 --port 4000 --config litellm_config.yaml
   
   # Terminal 2: Start FastAPI Server
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Install Chrome Extension**
   ```bash
   # Navigate to chrome://extensions/
   # Enable Developer mode
   # Click "Load unpacked" and select the /extension folder
   ```

### API Testing

Once both services are running, you can test the APIs using:
- **Swagger UI**: http://localhost:8000/docs (FastAPI interactive documentation)
- **LiteLLM UI**: http://localhost:4000 (LiteLLM proxy interface)

## API Documentation
    litellm_params:
      model: groq/mixtral-8x7b-32768
      api_key: env/GROQ_API_KEY
      
  - model_name: claude
    litellm_params:
      model: openrouter/anthropic/claude-3-sonnet
      api_key: env/OPENROUTER_API_KEY

general_settings:
  master_key: your-master-key
  database_url: postgresql://username:password@localhost:5432/litellm
```

## 📖 API Documentation

### Video Management

- `POST /videos` - Add new video from YouTube URL
- `GET /videos` - List all processed videos  
- `GET /videos/{id}/status` - Check video processing status
- `DELETE /videos/{id}` - Remove video and associated data

### Chat Operations

- `POST /chats` - Create new chat session for a video
- `GET /chats` - List all chat sessions
- `POST /chats/{id}/messages` - Send message and get AI response
- `GET /chats/{id}/history` - Retrieve chat history
- `DELETE /chats/{id}` - Delete chat session

### Example Usage

```bash
# Add a video
curl -X POST "http://localhost:8000/videos" \
  -H "Content-Type: application/json" \
  -d '{"youtube_link": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Create chat
curl -X POST "http://localhost:8000/chats" \
  -H "Content-Type: application/json" \
  -d '{"video_id": 1}'

# Send message
curl -X POST "http://localhost:8000/chats/1/messages" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the main topics discussed in this video?"}'
```

## Development

### Project Structure

```
AskTube/
├── extension/           # Chrome extension for YouTube integration
│   ├── manifest.json    # Extension configuration and permissions
│   ├── background.js    # Service worker for extension functionality
│   ├── api/            # API client for backend communication
│   └── pages/          # Extension UI pages (sidepanel, chat)
├── server/             # Python FastAPI backend
│   ├── src/
│   │   ├── controllers/ # Business logic and AI agent controllers
│   │   ├── models/     # Database models and schemas
│   │   ├── routes/     # API endpoints and route handlers
│   │   ├── stores/     # Vector database and LLM integrations
│   │   └── utils/      # Utility functions and settings
│   ├── requirements.txt # Python dependencies
│   └── litellm_config.yaml # LLM proxy configuration
└── README.md           # Project documentation
```

#### Key Directories Explained:

- **`extension/`**: Chrome browser extension providing YouTube integration and chat interface
- **`server/src/controllers/`**: Core business logic including the AI agent, NLP processing, and video management
- **`server/src/models/`**: SQLAlchemy database models, schemas, and enums for data structure
- **`server/src/routes/`**: FastAPI route definitions for videos, chats, and message endpoints
- **`server/src/stores/`**: Abstractions for external services (Pinecone vector DB, LiteLLM generation)
- **`server/src/utils/`**: Configuration management and utility functions

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature-name`
6. Submit a Pull Request

## Support & Contact

For any questions, issues, or contributions, please feel free to contact me or open an issue in the repository. I'm happy to help with setup, troubleshooting, or feature discussions.

## License

MIT License - see [LICENSE](LICENSE) file for details.