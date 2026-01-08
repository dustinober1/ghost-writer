# Changelog

## [Unreleased]

### Added
- **Ollama Support**: Added local LLM support via Ollama for free, private style rewriting
  - Supports OpenAI-compatible API format
  - Works with any Ollama model (llama2, mistral, phi, etc.)
  - No API keys required
  - Complete privacy (data never leaves your machine)
  - See `docs/OLLAMA_SETUP.md` for setup instructions

### Changed
- Updated `dspy_rewriter.py` to support three LLM backends:
  - OpenAI (cloud, requires API key)
  - Anthropic (cloud, requires API key)
  - Ollama (local, free, no API key)
- Model selection now configurable via `DEFAULT_LLM_MODEL` environment variable
- Improved error handling for Ollama connection issues

### Documentation
- Added `docs/OLLAMA_SETUP.md` with comprehensive setup guide
- Updated `README.md` to mention Ollama
- Updated `docs/QUICK_START.md` with Ollama configuration
- Updated `docs/NEXT_STEPS.md` with Ollama options

## [Initial Release]

### Features
- Stylometric fingerprinting engine
- AI vs human text detection
- Heat map visualization
- Personal fingerprint creation
- Style rewriting with DSPy
- User authentication
- Full-stack web application
