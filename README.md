# AskTube

AskTube is an AI-powered study assistant that helps users learn from YouTube videos using transcript and metadata. It leverages Retrieval-Augmented Generation (RAG) and integrates with LiteLLM, Pinecone, and FastAPI.

---

## Features

- Semantic search over video transcripts
- RAG-powered question answering
- FastAPI backend
- Pinecone vector database integration
- LiteLLM proxy for multi-provider LLM support

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/asktube.git
cd asktube/server
```

### 2. Create and activate a virtual environment

```bash
python -m venv env
env\Scripts\activate  # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

- Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

- Edit `.env` with your API keys and settings.

### 5. Configure LiteLLM

- Edit `litellm_config.yaml` to set up your models and provider keys.

### 6. Start LiteLLM Proxy

```bash
litellm --host 127.0.0.1 --port 4000 --config litellm_config.yaml
```

### 7. Start FastAPI server

```bash
uvicorn src.main:app --reload
```

---

## Usage

- Access API endpoints via FastAPI (see `src/routes/` for available routes).
- Use `/chat/search_and_generate` to get RAG-powered answers from your video transcript.

---

## Environment Variables

See `.env.example` for all required variables.

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

## License

MIT
