# Ollama Setup Guide

Ollama allows you to run large language models locally, providing a free alternative to cloud-based APIs for style rewriting.

## What is Ollama?

Ollama is a tool that lets you run LLMs on your local machine. It's perfect for:
- **Privacy**: Your data never leaves your machine
- **Cost**: No API costs
- **Offline**: Works without internet (after initial model download)
- **Customization**: Use any model that Ollama supports

## Installation

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
# Or download from https://ollama.ai/download
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download the installer from https://ollama.ai/download

### 2. Start Ollama Service

```bash
ollama serve
```

This starts the Ollama server on `http://localhost:11434` (default port).

### 3. Download a Model

Popular models for text rewriting:

```bash
# Llama 2 (7B parameters, good balance)
ollama pull llama2

# Llama 2 (13B parameters, better quality)
ollama pull llama2:13b

# Mistral (7B, fast and good quality)
ollama pull mistral

# CodeLlama (if you need code understanding)
ollama pull codellama

# Phi-2 (2.7B, very fast, smaller)
ollama pull phi
```

**Recommended for style rewriting:** `llama2` or `mistral`

## Configuration

### 1. Update `.env` file

Add these variables to `backend/.env`:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
DEFAULT_LLM_MODEL=ollama
```

### 2. Environment Variables

- **OLLAMA_BASE_URL**: Where Ollama is running (default: `http://localhost:11434`)
- **OLLAMA_MODEL**: Which model to use (e.g., `llama2`, `mistral`, `phi`)
- **DEFAULT_LLM_MODEL**: Set to `ollama` to use Ollama by default

### 3. Verify Ollama is Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test a simple request
ollama run llama2 "Hello, how are you?"
```

## Using Ollama in Ghostwriter

Ghostwriter now uses Ollama as the only provider for text embeddings and style rewriting. No API keys are required.

### Configuration

Set the following environment variables in your `.env` file:

```bash
OLLAMA_BASE_URL=http://localhost:11434  # Or your Ollama server URL
OLLAMA_MODEL=llama3.1:8b  # Or your preferred model
```

### Model Selection

You can switch between different Ollama models by changing `OLLAMA_MODEL`:
- `llama3.1:8b` - Balanced performance (default)
- `llama2:13b` - Higher quality (slower)
- `mistral` - Good performance/quality balance
- `phi` - Fast but lower quality
- Plus any other model you have pulled

See [Ollama Model Library](https://ollama.com/library) for more options.

## Performance Tips

### 1. Model Selection

- **Fast but lower quality**: `phi` (2.7B)
- **Balanced**: `llama2` (7B) or `mistral` (7B)
- **Better quality**: `llama2:13b` or `mistral:7b`
- **Best quality (slow)**: `llama2:70b` (requires significant RAM)

### 2. Hardware Requirements

- **Minimum**: 8GB RAM (for 7B models)
- **Recommended**: 16GB+ RAM (for 13B models)
- **GPU**: Optional but significantly faster (CUDA or Metal)

### 3. Speed Optimization

```bash
# Use smaller models for faster responses
OLLAMA_MODEL=phi

# Or use quantized versions
ollama pull llama2:7b-q4_0  # 4-bit quantization, faster
```

## Troubleshooting

### Ollama Not Starting

```bash
# Check if port is already in use
lsof -i :11434

# Start Ollama manually
ollama serve
```

### Model Not Found

```bash
# List available models
ollama list

# Pull the model again
ollama pull llama2
```

### Slow Performance

1. **Use a smaller model**: Switch to `phi` or `mistral:7b`
2. **Check system resources**: Ensure enough RAM/CPU available
3. **Use GPU**: Install CUDA (NVIDIA) or Metal (Apple Silicon)
4. **Reduce context**: Shorter input texts process faster

### Connection Errors

```bash
# Verify Ollama is accessible
curl http://localhost:11434/api/tags

# Check firewall settings
# Ensure port 11434 is not blocked
```

### Timeout Errors

Increase timeout in the code or use faster models. The default timeout is 120 seconds.

## Comparison: Ollama vs Cloud APIs

| Feature | Ollama | OpenAI | Anthropic |
|---------|--------|--------|-----------|
| Cost | Free | Pay per token | Pay per token |
| Privacy | 100% local | Cloud-based | Cloud-based |
| Speed | Depends on hardware | Fast | Fast |
| Internet | Not required | Required | Required |
| Setup | Easy | API key | API key |
| Quality | Good (model dependent) | Excellent | Excellent |

## Example Usage

### 1. Start Ollama

```bash
# Terminal 1
ollama serve
```

### 2. Pull Model (if not already done)

```bash
ollama pull llama2
```

### 3. Configure Ghostwriter

```bash
# In backend/.env
DEFAULT_LLM_MODEL=ollama
OLLAMA_MODEL=llama2
OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Use Style Rewriting

The rewrite feature will now use your local Ollama instance instead of cloud APIs.

## Advanced Configuration

### Custom Ollama Server

If running Ollama on a different machine:

```bash
OLLAMA_BASE_URL=http://192.168.1.100:11434
```

### Multiple Models

You can switch models by changing `OLLAMA_MODEL`:

```bash
# For faster responses
OLLAMA_MODEL=phi

# For better quality
OLLAMA_MODEL=llama2:13b
```

### Docker Setup

If you want to run Ollama in Docker:

```yaml
# Add to docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
```

## Next Steps

1. Install Ollama: https://ollama.ai/download
2. Pull a model: `ollama pull llama2`
3. Configure `.env` with Ollama settings
4. Test the rewrite feature
5. Enjoy free, local LLM rewriting!

For more information, visit: https://ollama.ai
