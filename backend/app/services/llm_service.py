"""
LLM service wrapper for interacting with Google Gemini AI models.
"""
from typing import List, Dict, Any
import google.generativeai as genai
from app.config.logging_config import get_logger
from app.config.settings import settings

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with Google Gemini Large Language Models."""
    
    def __init__(self):
        """Initialize LLM service with Gemini."""
        # Configure Gemini API
        genai.configure(api_key=settings.gemini_api_key)
        
        # Initialize model
        self.model_name = settings.gemini_model
        self.model = genai.GenerativeModel(self.model_name)
        
        # Safety settings (optional - adjust as needed)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        
        logger.info(f"LLMService initialized with Gemini model: {self.model_name}")
    
    async def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate completion from Gemini LLM.
        
        Args:
            system_prompt: System role prompt (context)
            user_prompt: User message
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails
        """
        try:
            logger.debug(f"Generating completion with Gemini model: {self.model_name}")
            
            # Combine system and user prompts
            # Gemini doesn't have separate system/user roles like OpenAI
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.95,
                top_k=40
            )
            
            # Generate content
            response = self.model.generate_content(
                combined_prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            
            # Extract text from response
            content = response.text
            
            logger.debug(f"Completion generated successfully. Length: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"Gemini completion failed: {str(e)}", exc_info=True)
            raise Exception(f"Gemini completion failed: {str(e)}")
    
    async def batch_generate(
        self,
        prompts: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> List[str]:
        """
        Generate multiple completions in batch.
        
        Args:
            prompts: List of prompt dictionaries with 'system' and 'user' keys
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
            
        Returns:
            List of generated texts
        """
        try:
            logger.info(f"Generating {len(prompts)} completions in batch")
            results = []
            
            for prompt in prompts:
                result = await self.generate_completion(
                    system_prompt=prompt.get('system', ''),
                    user_prompt=prompt.get('user', ''),
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                results.append(result)
            
            logger.info(f"Batch generation completed: {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Batch generation failed: {str(e)}", exc_info=True)
            raise Exception(f"Batch generation failed: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.
        
        Args:
            text: Input text
            
        Returns:
            Token count
        """
        try:
            token_count = self.model.count_tokens(text).total_tokens
            logger.debug(f"Token count: {token_count}")
            return token_count
        except Exception as e:
            logger.error(f"Token counting failed: {str(e)}")
            return 0