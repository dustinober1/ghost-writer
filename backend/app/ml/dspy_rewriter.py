"""
Ollama-powered style rewriting module.
Uses Ollama to rewrite AI-generated text to match user's style.
"""
import os
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()


class OllamaRewriter:
    """
    Ollama-powered rewriter that uses local LLM to rewrite text to match user's style.
    """
    
    def __init__(self):
        """
        Initialize Ollama rewriter.
        
        Uses environment variables for Ollama configuration:
        - OLLAMA_BASE_URL (default: http://localhost:11434)
        - OLLAMA_MODEL (default: llama3.1:8b)
        """
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        
        print(f"Ollama rewriter initialized with model: {self.ollama_model}")
    
    def rewrite_text(
        self,
        text: str,
        style_guidance: str,
        max_retries: int = 3
    ) -> str:
        """
        Rewrite text to match the target style using Ollama.
        
        Args:
            text: Text to rewrite
            style_guidance: Guidance on the target writing style
            max_retries: Maximum number of retries if rewriting fails
        
        Returns:
            Rewritten text
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if not style_guidance:
            style_guidance = "Maintain the original meaning while making the writing more natural and human-like."
        
        # Create style guidance prompt
        guidance_prompt = f"""
        Rewrite the following text to match this style:
        {style_guidance}
        
        Key style characteristics to match:
        - Natural variation in sentence length
        - Personal voice and tone
        - Human-like phrasing and word choice
        - Maintain the original meaning and key information
        """
        
        # Use Ollama API for rewriting
        return self._rewrite_with_ollama(text, guidance_prompt)
    
    def _rewrite_with_ollama(self, text: str, style_guidance: str) -> str:
        """Rewrite using Ollama API directly"""
        import requests
        
        prompt = f"""Rewrite the following text to match this style:
{style_guidance}

Original text:
{text}

Rewritten text:"""
        
        # Check if model exists first
        model_exists = self._check_ollama_model(self.ollama_base_url, self.ollama_model)
        if model_exists is False:
            raise ValueError(
                f"Model '{self.ollama_model}' not found in Ollama. "
                f"Please pull the model first with: ollama pull {self.ollama_model}"
            )
        
        # Use direct HTTP request to avoid compatibility issues
        # Try OpenAI-compatible chat endpoint first, then fall back to legacy endpoint
        try:
            # Try OpenAI-compatible chat endpoint first
            response = requests.post(
                f"{self.ollama_base_url}/v1/chat/completions",
                json={
                    "model": self.ollama_model,
                    "messages": [
                        {"role": "system", "content": "You are a writing style expert who rewrites text to match specific styles while preserving meaning."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 404:
                # Model not found, try legacy endpoint
                raise requests.exceptions.HTTPError("404 Model not found", response=response)
            
            response.raise_for_status()
            result = response.json()
            
            # Check if we got a valid response
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"].strip()
            elif "message" in result and "content" in result["message"]:
                return result["message"]["content"].strip()
            else:
                # Unexpected response format, fall back to legacy endpoint
                raise ValueError("Unexpected response format")
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 404:
                # Model not found, provide helpful error
                raise ValueError(
                    f"Model '{self.ollama_model}' not found in Ollama at {self.ollama_base_url}. "
                    f"Please ensure the model is pulled: ollama pull {self.ollama_model}"
                )
            # Try legacy /api/generate endpoint as fallback
            try:
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": f"You are a writing style expert. {prompt}",
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 2000
                        }
                    },
                    timeout=120
                )
                
                if response.status_code == 404:
                    raise ValueError(
                        f"Model '{self.ollama_model}' not found in Ollama at {self.ollama_base_url}. "
                        f"Please ensure the model is pulled: ollama pull {self.ollama_model}"
                    )
                
                response.raise_for_status()
                return response.json()["response"].strip()
            except requests.exceptions.HTTPError as fallback_http_error:
                if fallback_http_error.response and fallback_http_error.response.status_code == 404:
                    raise ValueError(
                        f"Model '{self.ollama_model}' not found in Ollama at {self.ollama_base_url}. "
                        f"Please ensure the model is pulled: ollama pull {self.ollama_model}"
                    )
                raise ValueError(f"Error with Ollama API: {str(fallback_http_error)}")
            except requests.exceptions.ConnectionError:
                raise ValueError(
                    f"Cannot connect to Ollama at {self.ollama_base_url}. "
                    "Please ensure Ollama is running. You can start it with: ollama serve"
                )
            except requests.exceptions.Timeout:
                raise ValueError(
                    f"Ollama request timed out after 120 seconds. "
                    f"The server at {self.ollama_base_url} may be too slow or unavailable."
                )
            except ValueError as ve:
                # Re-raise ValueError as-is
                raise ve
            except Exception as fallback_error:
                raise ValueError(f"Error with Ollama API: {str(fallback_error)}")
        except requests.exceptions.ConnectionError:
            raise ValueError(
                f"Cannot connect to Ollama at {self.ollama_base_url}. "
                "Please ensure Ollama is running. You can start it with: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise ValueError(
                f"Ollama request timed out after 120 seconds. "
                f"The server at {self.ollama_base_url} may be too slow or unavailable."
            )
        except ValueError as ve:
            # Re-raise ValueError as-is
            raise ve
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                raise ValueError(
                    f"Model '{self.ollama_model}' not found in Ollama at {self.ollama_base_url}. "
                    f"Please ensure the model is pulled: ollama pull {self.ollama_model}"
                )
            elif "Connection" in error_msg or "refused" in error_msg.lower() or "connect" in error_msg.lower():
                raise ValueError(
                    f"Cannot connect to Ollama at {self.ollama_base_url}. "
                    "Please ensure Ollama is running. You can start it with: ollama serve"
                )
            elif "timeout" in error_msg.lower():
                raise ValueError(
                    f"Ollama request timed out. "
                    f"The server at {self.ollama_base_url} may be too slow or unavailable."
                )
            else:
                raise ValueError(f"Error with Ollama API: {error_msg}")
    
    def _check_ollama_model(self, ollama_base_url: str, ollama_model: str) -> bool:
        """Check if a model exists in Ollama"""
        try:
            import requests
            response = requests.get(
                f"{ollama_base_url}/api/tags",
                timeout=10
            )
            response.raise_for_status()
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            # Check if exact match or model with tag exists
            return ollama_model in model_names or any(
                model_name.startswith(f"{ollama_model}:") or model_name == ollama_model
                for model_name in model_names
            )
        except Exception:
            # If we can't check, assume model might exist and let the API call fail
            return None
    
    def rewrite_with_fingerprint(
        self,
        text: str,
        fingerprint: Dict,
        max_retries: int = 3
    ) -> str:
        """
        Rewrite text to match user's fingerprint style.
        
        Args:
            text: Text to rewrite
            fingerprint: User's fingerprint dictionary
            max_retries: Maximum number of retries
        
        Returns:
            Rewritten text
        """
        # Generate style guidance from fingerprint
        style_guidance = self._generate_style_guidance(fingerprint)
        
        return self.rewrite_text(text, style_guidance, max_retries)
    
    def _generate_style_guidance(self, fingerprint: Dict) -> str:
        """
        Generate style guidance from fingerprint features.
        
        Args:
            fingerprint: Fingerprint dictionary
        
        Returns:
            Style guidance string
        """
        # Extract features from fingerprint
        features = fingerprint.get("feature_vector", [])
        
        # Generate guidance based on feature characteristics
        guidance_parts = [
            "Match the following writing style characteristics:",
            "- Maintain natural variation in sentence structure",
            "- Use similar vocabulary patterns and word choice",
            "- Preserve the author's unique voice and tone",
            "- Keep the same level of formality and complexity"
        ]
        
        return "\n".join(guidance_parts)


# Global rewriter instance (lazy loading)
_rewriter_instance = None


def get_ollama_rewriter() -> OllamaRewriter:
    """Get or create the global Ollama rewriter instance"""
    global _rewriter_instance
    
    if _rewriter_instance is None:
        _rewriter_instance = OllamaRewriter()
    
    return _rewriter_instance


# Backwards compatibility alias
def get_dspy_rewriter(model: Optional[str] = None):
    """
    Backwards compatibility alias.
    Now always returns OllamaRewriter regardless of model parameter.
    """
    if model and model not in ["ollama", None]:
        print(f"Warning: Model '{model}' is no longer supported. Using Ollama instead.")
    return get_ollama_rewriter()


# Backwards compatibility alias for class
DSPyRewriter = OllamaRewriter
