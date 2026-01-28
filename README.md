# <img src="frontend/public/arke-icon-crop.png" width="60" height="64"> Arke

**A fast, efficient, locally-run Retrieval-Augmented Generation (RAG) system for document querying and knowledge base management**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.txt)
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/dassoo)

<video src="https://raw.githubusercontent.com/Dassoo/Arke/blob/main/demo.mp4" width="640" height="480" controls></video>

Arke is a small personal project focused on building a local high-performance RAG system by combining some of the most modern and efficient tools and libraries available.

> Note: As a design choice, chat threads lack persistence across backend resets. Only document storage and cached embeddings, along with document and query caching, are retained. This accommodates users who often open chats and forget about them, automatically cleaning up excess information.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Frontend](#frontend)
- [Configuration](#configuration)
- [License](#license)

## Features

- **Agent-Driven Architecture**: Built around a LangChain agent enhanced with custom tools for intelligent document ingestion and querying
- **High-Performance Storage & Retrieval**: Qdrant-backed vector store optimized for fast, scalable semantic search
- **Intelligent Caching Strategy**: Dual-layer caching with local embedding persistence to minimize latency and cost (Redis + LangChain native)
- **Ultra-Fast Multiformat Ingestion**: Native support for 50+ document formats powered by the Rust-based Kreuzberg OCR engine
- **Modern Web Interface**: Next.js frontend with real-time streaming responses

## Prerequisites

- Python 3.12 or higher
- Node.js 18+
- OpenAI API key
- Docker

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd arke
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   # or if using uv
   uv sync
   ```

3. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```

4. **Start vector databases with Docker:**
   A `docker-compose.yml` file is provided to spin up both Redis and Qdrant instances:

   ```bash
   docker compose up -d
   ```

5. **Set up environment variables:**
   Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```

   Required variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `REDIS_URL`: Redis connection URL (default:  `redis://localhost:6379`)
   - `QDRANT_URL`: Qdrant connection URL (default:  `http://localhost:6333`)

## Usage

### Backend Server

1. **Start the FastAPI server:**
   ```bash
   python src/main.py
   # or if using uv
   uv run python src/main.py
   ```

### Frontend Application

1. **Start the Next.js development server:**
   ```bash
   cd frontend
   npm run dev
   ```
   The frontend will be available at `http://localhost:3000`


2. **Interact with the system:**
   - **Store documents**: Specify folder paths with the documents to add (providing a sample in 'data/greece_dataset')
   - **Query knowledge base**: Ask questions about stored documents
   - **Manage documents**: View, delete stored documents or flush the database

## Configuration

You can eventually customize the system settings through `src/core/config.py`:

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---
