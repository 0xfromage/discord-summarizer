"""
Summarizer Factory Module

This module provides a factory function for creating LLM summarizers and
handles the dynamic selection of appropriate summarizer classes based on 
the configured provider.
"""

import logging
from typing import Optional

from config.settings import LLMProvider, LLMConfig
from summarizers.base import BaseSummarizer
from summarizers.deepseek import DeepSeekSummarizer
from summarizers.anthropic import AnthropicSummarizer

logger = logging.getLogger(__name__)

def create_summarizer(config: LLMConfig) -> BaseSummarizer:
    """
    Factory function to create the appropriate LLM summarizer based on the configuration.
    
    Args:
        config: LLM configuration
        
    Returns:
        BaseSummarizer: An instantiated summarizer object
        
    Raises:
        ValueError: If an unsupported LLM provider is specified
    """
    logger.info(f"Creating summarizer for provider: {config.provider}")
    
    if config.provider == LLMProvider.DEEPSEEK:
        return DeepSeekSummarizer(config.api_key)
    elif config.provider == LLMProvider.ANTHROPIC:
        return AnthropicSummarizer(config.api_key)
    else:
        error_msg = f"Unsupported LLM provider: {config.provider}"
        logger.error(error_msg)
        raise ValueError(error_msg)