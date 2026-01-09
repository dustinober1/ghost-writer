# Changelog

## [Unreleased]

### Changed
- **Ollama-Only Architecture**: Removed OpenAI and Anthropic support
  - Now uses Ollama for all text analysis and rewriting
  - Removed `openai` and `anthropic` package dependencies
  - Removed OpenAI/Anthropic API key configuration from Docker files
  - Simplified rewriter to use only Ollama
  - Updated perplexity calculation to use Ollama API with fallback to heuristic
  - Removed embedder selection UI (always uses Ollama embeddings)
  - Updated all documentation to reflect Ollama-only setup

### Added
- **Ollama Integration**:
  - Supports Ollama for text embeddings and style rewriting
  - Works with any Ollama model (llama3.1:8b, mistral, phi, etc.)
  - No API keys required for Ollama
  - Complete privacy (data never leaves your machine)
  - See `docs/OLLAMA_SETUP.md` for setup instructions

### Documentation
- Added `docs/OLLAMA_SETUP.md` with comprehensive setup guide
- Updated `README.md` to mention Ollama as the LLM provider
- Updated `docs/QUICK_START.md` with Ollama configuration instructions
- Updated `docs/NEXT_STEPS.md` with simplified Ollama-only setup
- Updated `docs/DOCKER_SETUP.md` to remove OpenAI/Anthropic env vars

## [Initial Release]

### Features
- Stylometric fingerprinting engine
- AI vs human text detection
- Heat map visualization
- Personal fingerprint creation
- Style rewriting with DSPy
- User authentication
- Full-stack web application
