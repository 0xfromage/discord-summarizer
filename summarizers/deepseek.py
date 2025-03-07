import logging
from openai import OpenAI
from summarizers.base import BaseSummarizer
from utils.prompts import PromptTemplates

# Get logger
logger = logging.getLogger(__name__)

class DeepSeekSummarizer(BaseSummarizer):
    """DeepSeek implementation of the summarizer using OpenAI-compatible format"""
    
    def __init__(self, api_key):
        """
        Initialize with API key
        
        Args:
            api_key (str): DeepSeek API key
        """
        super().__init__(api_key)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
    
    def generate_summary(
        self, 
        message_texts, 
        topic_name=None,  # Changed parameter name from channel_name to topic_name
        prompt_type=None, 
        override_system_prompt=None, 
        override_user_prompt=None
    ):
        try:
            # Combine messages
            combined_text = "\n".join(message_texts)
            
            # Limit combined text length
            max_tokens = 12000  # DeepSeek has smaller context window
            if len(combined_text) > max_tokens:
                logger.warning(f"Truncating message text from {len(combined_text)} to {max_tokens} characters")
                combined_text = combined_text[-max_tokens:]
            
            # Get appropriate prompts with potential overrides
            prompts = PromptTemplates.get_prompts(
                topic_name=topic_name,  # Parameter name matches what PromptTemplates expects
                prompt_type=prompt_type,
                override_system_prompt=override_system_prompt,
                override_user_prompt=override_user_prompt
            )
            
            # Log message count
            logger.info(f"Sending {len(message_texts)} messages to DeepSeek API")
            
            # Use OpenAI-compatible format for DeepSeek
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system", 
                        "content": prompts['system_prompt']
                    },
                    {
                        "role": "user", 
                        "content": PromptTemplates.format_user_prompt(
                            combined_text, 
                            topic_name=topic_name,  # Parameter name matches what PromptTemplates expects
                            prompt_type=prompt_type,
                            override_system_prompt=override_system_prompt,
                            override_user_prompt=override_user_prompt
                        )
                    }
                ],
                max_tokens=1000
            )
            
            logger.info("Successfully received response from DeepSeek API")
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f'DeepSeek summary generation error: {e}')
            return f"Unable to generate summary with DeepSeek. Error: {str(e)}"