---
created: 2026-01-19T16:15
title: Download Ollama models for AI detection
area: infrastructure
files:
  - docker-compose.yml:55-89
---

## Problem

Ollama service is running in Docker but models (llama3:8b, nomic-embed-text:v1.5) are not downloaded. This causes:
- 500 Server Error when backend tries to use Ollama embeddings
- Fallback to stylometric heuristics only
- Full AI detection pipeline not functional

Backend logs show:
```
Warning: Error calculating perplexity with Ollama: 500 Server Error: Internal Server Error for url: http://ollama:11434/api/generate. Using heuristic.
Warning: Error getting Ollama embedding: 500 Server Error: Internal Server Error for url: http://ollama:11434/api/embeddings. Falling back to stylometric.
```

## Solution

Models need to be pulled after Ollama container starts:

```bash
docker exec -it ghostwriter_ollama ollama pull llama3:8b
docker exec -it ghostwriter_ollama ollama pull nomic-embed-text:v1.5
```

Total download size: ~4GB

Consider adding to setup documentation or creating init script for automated pulling.
