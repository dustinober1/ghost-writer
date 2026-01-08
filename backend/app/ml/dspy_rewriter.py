"""
DSPy-powered style rewriting module.
Uses DSPy to optimize LLM calls for rewriting AI-generated text to match user's style.
"""
import os
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

# Try to import dspy, with fallback if not available
try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    print("Warning: DSPy not available. Style rewriting will use fallback method.")


class StyleRewriter:
    """DSPy signature for style rewriting task"""
    if DSPY_AVAILABLE:
        class StyleRewriterSignature(dspy.Signature):
            """DSPy signature for style rewriting task"""
            original_text: str = dspy.InputField(desc="The original AI-generated text to rewrite")
            style_guidance: str = dspy.InputField(desc="Guidance on the target writing style")
            rewritten_text: str = dspy.OutputField(desc="Text rewritten to match the target style")
        
        Signature = StyleRewriterSignature
    else:
        Signature = None


class DSPyRewriter:
    """
    DSPy-powered rewriter that uses LLMs to rewrite text to match user's style.
    Falls back to direct API calls if DSPy is not available.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize DSPy rewriter.
        
        Args:
            model: Model to use ("openai", "anthropic", or "ollama"). Defaults to Ollama if no API keys are found.
        """
        default_model = os.getenv("DEFAULT_LLM_MODEL", "ollama")
        self.model_name = model or default_model
        
        # If OpenAI/Anthropic is selected but no API key, fall back to Ollama
        if self.model_name == "openai" and not os.getenv("OPENAI_API_KEY"):
            print("Warning: OPENAI_API_KEY not found. Falling back to Ollama.")
            self.model_name = "ollama"
        elif self.model_name == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
            print("Warning: ANTHROPIC_API_KEY not found. Falling back to Ollama.")
            self.model_name = "ollama"
        
        self.rewriter = None
        self.lm = None
        
        if DSPY_AVAILABLE:
            self._setup_lm()
            if StyleRewriter.Signature:
                self.rewriter = dspy.ChainOfThought(StyleRewriter.Signature)
        else:
            print("DSPy not available. Using fallback rewriting method.")
    
    def _setup_lm(self):
        """Setup the language model for DSPy"""
        if not DSPY_AVAILABLE:
            return
            
        try:
            if self.model_name == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment variables")
                # DSPy uses OpenAI client directly
                import openai
                self.lm = dspy.LM(model="gpt-4", api_key=api_key)
            elif self.model_name == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
                # DSPy may need different setup for Anthropic
                self.lm = dspy.LM(model="claude-3-opus-20240229", api_key=api_key)
            elif self.model_name == "ollama":
                # Ollama uses OpenAI-compatible API
                ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
                ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
                try:
                    # DSPy may not support custom base URLs directly
                    # So we'll use fallback mode for Ollama
                    print("Ollama selected. Using direct API calls (DSPy may not support custom base URLs).")
                    self.lm = None
                    self.rewriter = None
                except Exception as e:
                    print(f"Warning: Could not setup Ollama with DSPy: {e}")
                    print("Falling back to direct API calls.")
                    self.lm = None
                    self.rewriter = None
            else:
                raise ValueError(f"Unsupported model: {self.model_name}. Supported: openai, anthropic, ollama")
            
            dspy.configure(lm=self.lm)
        except Exception as e:
            print(f"Warning: Could not setup DSPy LM: {e}")
            print("Falling back to direct API calls.")
            self.lm = None
            self.rewriter = None
    
    def rewrite_text(
        self,
        text: str,
        style_guidance: str,
        max_retries: int = 3
    ) -> str:
        """
        Rewrite text to match the target style.
        
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
        
        # Use DSPy if available, otherwise fallback to direct API
        if self.rewriter and DSPY_AVAILABLE:
            try:
                result = self.rewriter(
                    original_text=text,
                    style_guidance=guidance_prompt
                )
                return result.rewritten_text
            except Exception as e:
                if max_retries > 0:
                    return self.rewrite_text(text, style_guidance, max_retries - 1)
                # Fallback to direct API
                return self._rewrite_with_direct_api(text, style_guidance)
        else:
            # Use direct API call as fallback
            return self._rewrite_with_direct_api(text, style_guidance)
    
    def _rewrite_with_direct_api(self, text: str, style_guidance: str) -> str:
        """
        Fallback method using direct API calls when DSPy is not available.
        """
        if self.model_name == "openai":
            return self._rewrite_with_openai(text, style_guidance)
        elif self.model_name == "anthropic":
            return self._rewrite_with_anthropic(text, style_guidance)
        elif self.model_name == "ollama":
            return self._rewrite_with_ollama(text, style_guidance)
        else:
            raise ValueError(f"Unsupported model: {self.model_name}. Supported: openai, anthropic, ollama")
    
    def _rewrite_with_openai(self, text: str, style_guidance: str) -> str:
        """Rewrite using OpenAI API directly"""
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found. Please set OPENAI_API_KEY environment variable.")
        
        try:
            client = openai.OpenAI(api_key=api_key)
            
            prompt = f"""Rewrite the following text to match this style:
{style_guidance}

Original text:
{text}

Rewritten text:"""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a writing style expert who rewrites text to match specific styles while preserving meaning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
        except openai.AuthenticationError as e:
            raise ValueError(f"OpenAI authentication failed: {str(e)}. Please check your API key.")
        except openai.RateLimitError as e:
            raise ValueError(f"OpenAI rate limit exceeded: {str(e)}. Please try again later.")
        except openai.APIError as e:
            raise ValueError(f"OpenAI API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error with OpenAI API: {str(e)}")
    
    def _rewrite_with_anthropic(self, text: str, style_guidance: str) -> str:
        """Rewrite using Anthropic API directly"""
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Please set ANTHROPIC_API_KEY environment variable.")
        
        try:
            client = anthropic.Anthropic(api_key=api_key)
            
            prompt = f"""Rewrite the following text to match this style:
{style_guidance}

Original text:
{text}

Rewritten text:"""
            
            message = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text.strip()
        except anthropic.AuthenticationError as e:
            raise ValueError(f"Anthropic authentication failed: {str(e)}. Please check your API key.")
        except anthropic.RateLimitError as e:
            raise ValueError(f"Anthropic rate limit exceeded: {str(e)}. Please try again later.")
        except anthropic.APIError as e:
            raise ValueError(f"Anthropic API error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error with Anthropic API: {str(e)}")
    
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
    
    def _rewrite_with_ollama(self, text: str, style_guidance: str) -> str:
        """Rewrite using Ollama API directly"""
        import requests
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        
        prompt = f"""Rewrite the following text to match this style:
{style_guidance}

Original text:
{text}

Rewritten text:"""
        
        # Check if model exists first
        model_exists = self._check_ollama_model(ollama_base_url, ollama_model)
        if model_exists is False:
            raise ValueError(
                f"Model '{ollama_model}' not found in Ollama. "
                f"Please pull the model first with: ollama pull {ollama_model}"
            )
        
        # Use direct HTTP request to avoid OpenAI client compatibility issues
        # Try OpenAI-compatible chat endpoint first, then fall back to legacy endpoint
        try:
            # Try OpenAI-compatible chat endpoint first
            response = requests.post(
                f"{ollama_base_url}/v1/chat/completions",
                json={
                    "model": ollama_model,
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
                    f"Model '{ollama_model}' not found in Ollama at {ollama_base_url}. "
                    f"Please ensure the model is pulled: ollama pull {ollama_model}"
                )
            # Try legacy /api/generate endpoint as fallback
            try:
                response = requests.post(
                    f"{ollama_base_url}/api/generate",
                    json={
                        "model": ollama_model,
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
                        f"Model '{ollama_model}' not found in Ollama at {ollama_base_url}. "
                        f"Please ensure the model is pulled: ollama pull {ollama_model}"
                    )
                
                response.raise_for_status()
                return response.json()["response"].strip()
            except requests.exceptions.HTTPError as fallback_http_error:
                if fallback_http_error.response and fallback_http_error.response.status_code == 404:
                    raise ValueError(
                        f"Model '{ollama_model}' not found in Ollama at {ollama_base_url}. "
                        f"Please ensure the model is pulled: ollama pull {ollama_model}"
                    )
                raise ValueError(f"Error with Ollama API: {str(fallback_http_error)}")
            except requests.exceptions.ConnectionError:
                raise ValueError(
                    f"Cannot connect to Ollama at {ollama_base_url}. "
                    "Please ensure Ollama is running. You can start it with: ollama serve"
                )
            except requests.exceptions.Timeout:
                raise ValueError(
                    f"Ollama request timed out after 120 seconds. "
                    f"The server at {ollama_base_url} may be too slow or unavailable."
                )
            except ValueError as ve:
                # Re-raise ValueError as-is
                raise ve
            except Exception as fallback_error:
                raise ValueError(f"Error with Ollama API: {str(fallback_error)}")
        except requests.exceptions.ConnectionError:
            raise ValueError(
                f"Cannot connect to Ollama at {ollama_base_url}. "
                "Please ensure Ollama is running. You can start it with: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise ValueError(
                f"Ollama request timed out after 120 seconds. "
                f"The server at {ollama_base_url} may be too slow or unavailable."
            )
        except ValueError as ve:
            # Re-raise ValueError as-is
            raise ve
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                raise ValueError(
                    f"Model '{ollama_model}' not found in Ollama at {ollama_base_url}. "
                    f"Please ensure the model is pulled: ollama pull {ollama_model}"
                )
            elif "Connection" in error_msg or "refused" in error_msg.lower() or "connect" in error_msg.lower():
                raise ValueError(
                    f"Cannot connect to Ollama at {ollama_base_url}. "
                    "Please ensure Ollama is running. You can start it with: ollama serve"
                )
            elif "timeout" in error_msg.lower():
                raise ValueError(
                    f"Ollama request timed out. "
                    f"The server at {ollama_base_url} may be too slow or unavailable."
                )
            else:
                raise ValueError(f"Error with Ollama API: {error_msg}")
    
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
        # Extract key characteristics from fingerprint features
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


def get_dspy_rewriter(model: Optional[str] = None) -> DSPyRewriter:
    """Get or create the global DSPy rewriter instance"""
    global _rewriter_instance
    
    if _rewriter_instance is None:
        try:
            _rewriter_instance = DSPyRewriter(model=model)
        except Exception as e:
            # If initialization fails, create a fallback instance
            print(f"Warning: Could not initialize DSPy rewriter: {e}")
            print("Using fallback mode (direct API calls)")
            _rewriter_instance = DSPyRewriter(model=model)
            # Force fallback mode
            _rewriter_instance.rewriter = None
            _rewriter_instance.lm = None
    
    return _rewriter_instance
