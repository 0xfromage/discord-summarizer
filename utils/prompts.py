"""
Prompt Management Module

This module provides templates and formatting for generating prompts
for different LLM providers and use cases.
"""

from typing import Dict, Optional, Any

class PromptTemplates:
    """
    A collection of prompt templates for different summarization contexts.
    """

    DEFAULT_SYSTEM_PROMPT: str = """
    You are an expert Discord conversation summarizer who excels at extracting key information from chat discussions.

    When summarizing Discord conversations, follow these guidelines:
    1. Identify the main topics, themes, and important discussions
    2. Highlight key points, decisions, questions, and announcements
    3. Maintain objectivity while capturing the tone of the conversation
    4. Organize information in a clear, structured format
    5. Focus on actionable and meaningful content
    6. Provide enough context for someone who missed the conversation
    7. Be concise but comprehensive

    Your summary should be well-organized, easy to read, and capture the essence of the conversation.
    """

    DEFAULT_USER_PROMPT: str = """
    Please summarize the following Discord conversation from the channel "{channel_name}".

    Focus on extracting the most important information, main discussion topics, decisions made, questions asked, 
    and any actionable items. Organize the summary in a clear and structured way.

    CONVERSATION:
    {text}

    Please provide a comprehensive yet concise summary that would be helpful for someone who missed this conversation.
    """

    SPECIALIZED_PROMPTS: Dict[str, Dict[str, str]] = {
        'general': {
            'system_prompt': DEFAULT_SYSTEM_PROMPT,
            'user_prompt': DEFAULT_USER_PROMPT
        },
        'technical': {
            'system_prompt': """
            You are an expert technical summarizer who specializes in extracting key information from technical Discord discussions.
            
            When summarizing technical conversations, follow these guidelines:
            1. Focus on technical details, code discussions, and implementation specifics
            2. Highlight technical decisions, approaches, and solutions
            3. Identify bugs, issues, and their proposed solutions
            4. Note any technical questions that remain unanswered
            5. Include links to resources, documentation, or external references
            6. Maintain accuracy when describing technical concepts
            7. Organize information by topic or component
            """,
            'user_prompt': """
            Please provide a technical summary of the following Discord conversation from the channel "{channel_name}".
            
            Focus on technical details, code discussions, implementation approaches, issues/bugs, 
            and technical decisions. Include any shared resource links or references.
            
            CONVERSATION:
            {text}
            
            Please organize the summary by technical topics or components discussed, highlighting key decisions and open questions.
            """
        },
        'gaming': {
            'system_prompt': """
            You are an expert gaming community summarizer who specializes in extracting key information from gaming-related Discord discussions.
            
            When summarizing gaming conversations, follow these guidelines:
            1. Highlight game updates, patch notes, and announcements
            2. Summarize gameplay discussions, strategies, and tips
            3. Note community events, tournaments, and meetups
            4. Include discussions about game mechanics, characters, and features
            5. Capture community feedback, suggestions, and concerns
            6. Mention any official responses from game developers or community managers
            7. Organize information by game, topic, or event
            """,
            'user_prompt': """
            Please summarize the following gaming-related Discord conversation from the channel "{channel_name}".
            
            Focus on game updates, gameplay discussions, community events, strategies, feedback, and any official announcements.
            
            CONVERSATION:
            {text}
            
            Please organize the summary by topics, highlighting key information that would be valuable for gaming community members.
            """
        }
    }

    @classmethod
    def get_prompts(
        cls, 
        channel_name: Optional[str] = None, 
        prompt_type: Optional[str] = None, 
        override_system_prompt: Optional[str] = None, 
        override_user_prompt: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get appropriate prompts for the given context.
        
        Args:
            channel_name: Name of the Discord channel
            prompt_type: Type of prompt to use (e.g., 'technical', 'gaming')
            override_system_prompt: Custom system prompt to use
            override_user_prompt: Custom user prompt to use
            
        Returns:
            Dictionary with 'system_prompt' and 'user_prompt' keys
        """
        # Select the base prompts
        if prompt_type and prompt_type in cls.SPECIALIZED_PROMPTS:
            prompts = cls.SPECIALIZED_PROMPTS[prompt_type]
        elif channel_name:
            # Try to infer prompt type from channel name
            channel_lower = channel_name.lower()
            
            if any(tech in channel_lower for tech in ['dev', 'code', 'programming', 'tech', 'engineering']):
                prompts = cls.SPECIALIZED_PROMPTS['technical']
            elif any(game in channel_lower for game in ['game', 'gaming', 'play', 'stream']):
                prompts = cls.SPECIALIZED_PROMPTS['gaming']
            else:
                prompts = cls.SPECIALIZED_PROMPTS['general']
        else:
            prompts = cls.SPECIALIZED_PROMPTS['general']
        
        # Apply overrides if provided
        result = {
            'system_prompt': override_system_prompt or prompts['system_prompt'],
            'user_prompt': override_user_prompt or prompts['user_prompt']
        }
        
        return result

    @classmethod
    def format_user_prompt(
        cls, 
        text: str, 
        channel_name: str = "Discord Channel",
        prompt_type: Optional[str] = None
    ) -> str:
        """
        Format the user prompt with the given text and channel name.
        
        Args:
            text: The conversation text to summarize
            channel_name: Name of the Discord channel
            prompt_type: Type of prompt to use
            
        Returns:
            Formatted user prompt
        """
        prompts = cls.get_prompts(channel_name=channel_name, prompt_type=prompt_type)
        return prompts['user_prompt'].format(text=text, channel_name=channel_name)