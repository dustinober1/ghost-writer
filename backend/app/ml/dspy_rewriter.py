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
            model: Model to use ("openai" or "anthropic"). Defaults to OpenAI.
        """
        self.model_name = model or "openai"
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
            else:
                raise ValueError(f"Unsupported model: {self.model_name}")
            
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
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")
    
    def _rewrite_with_openai(self, text: str, style_guidance: str) -> str:
        """Rewrite using OpenAI API directly"""
        try:
            import openai
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found")
            
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
        except Exception as e:
            raise Exception(f"Error with OpenAI API: {str(e)}")
    
    def _rewrite_with_anthropic(self, text: str, style_guidance: str) -> str:
        """Rewrite using Anthropic API directly"""
        try:
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found")
            
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
        except Exception as e:
            raise Exception(f"Error with Anthropic API: {str(e)}")
    
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
        _rewriter_instance = DSPyRewriter(model=model)
    
    return _rewriter_instance
