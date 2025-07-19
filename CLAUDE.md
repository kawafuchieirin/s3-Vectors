# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

s3-Vectors is a RAG (Retrieval-Augmented Generation) system for creating sales proposals using Amazon S3 Vectors and Amazon Bedrock. The system allows users to upload sales documents, vectorize them, and generate customized proposals based on stored knowledge.

## Project Structure

```
s3-Vectors/
├── src/
│   ├── api/           # FastAPI REST API
│   ├── core/          # Core business logic
│   │   ├── config.py           # Configuration management
│   │   ├── document_processor.py # Document processing and chunking
│   │   ├── embeddings.py       # Bedrock embedding service
│   │   ├── vector_store.py     # S3 Vectors integration
│   │   └── rag_engine.py       # RAG implementation
│   ├── utils/         # Utility functions
│   └── web/           # Web interface components
├── tests/             # Test files
├── data/              # Data storage
│   ├── raw/          # Original documents
│   └── processed/    # Processed data
├── streamlit_app.py   # Streamlit UI
└── docker-compose.yml # Docker configuration
```

## Development Commands

### Setup
```bash
# Initial setup
./scripts/setup.sh

# Install dependencies
poetry install

# Copy and configure environment variables
cp .env.example .env
```

### Running the Application

```bash
# Start API server
poetry run uvicorn src.api.main:app --reload

# Start Streamlit UI
poetry run streamlit run streamlit_app.py

# Or use Docker Compose
docker-compose up
```

### Testing and Linting
```bash
# Run tests
poetry run pytest

# Format code
poetry run black src/

# Lint code
poetry run flake8 src/

# Type checking
poetry run mypy src/
```

## Architecture

### Core Components

1. **Document Processor**: Handles PDF, DOCX, and text files, chunks them for vectorization
2. **S3 Vector Store**: Manages vector storage and retrieval using Amazon S3 Vectors
3. **RAG Engine**: Combines search and generation for creating proposals
4. **FastAPI Backend**: RESTful API for document management and proposal generation
5. **Streamlit Frontend**: User-friendly web interface

### Key Technologies

- **Python 3.9+**: Main programming language
- **Amazon S3 Vectors**: Vector storage (currently in preview)
- **Amazon Bedrock**: Embeddings and text generation
- **FastAPI**: REST API framework
- **Streamlit**: Web UI framework
- **Poetry**: Dependency management

## Important Notes

1. **S3 Vectors API**: As of the implementation, S3 Vectors is in preview. Some API methods (create_vector_index, put_vectors, query_vectors) are placeholders and need to be updated when the official SDK support is available.

2. **Environment Variables**: Ensure all AWS credentials and S3 Vectors configuration are properly set in the .env file

3. **File Types**: Currently supports PDF, DOCX, DOC, TXT, and MD files for upload

4. **Chunking Strategy**: Uses RecursiveCharacterTextSplitter with configurable chunk size and overlap