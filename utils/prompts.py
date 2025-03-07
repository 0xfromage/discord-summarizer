"""
Improved Prompt Management with DeFi and Crypto Focus

Enhanced prompts focused on crypto, DeFi, yield farming, and financial strategies.
Both specialized and default prompts now include handling of data and links.
"""

from typing import Dict, Optional, Any

class PromptTemplates:
    """
    A sophisticated prompt management system for LLM summarization.

    This class provides a flexible mechanism for generating and customizing 
    prompts based on context, topic, and specific requirements.

    Attributes:
        DEFAULT_SYSTEM_PROMPT (str): A generic system prompt for basic summarization.
        DEFAULT_USER_PROMPT (str): A standard template for formatting user input.
        SPECIALIZED_PROMPTS (Dict[str, Dict[str, str]]): A collection of context-specific prompts.
    """

    DEFAULT_SYSTEM_PROMPT: str = """
    You are an expert summarization assistant designed to extract 
    key insights from complex conversations.

    Core Summarization Guidelines:
    1. Identify the most significant information
    2. Maintain objectivity and precision
    3. Provide clear, structured insights
    4. Focus on actionable and meaningful content
    5. Adapt to the specific context of the conversation
    6. Include all relevant links that were shared in the discussion
    7. If data or statistics are mentioned, analyze and highlight them when relevant
    8. Pay attention to financial strategies, trading ideas, or investment opportunities mentioned
    9. DATA IS KEY
    """

    DEFAULT_USER_PROMPT: str = """
    Analyze and summarize the following conversation with careful attention 
    to context, key themes, and important details.

    Conversation Transcript:
    {text}

    Summary Expectations:
    - Concise yet comprehensive overview
    - Highlight main topics and notable interactions
    - Capture essential insights and potential implications
    - Maintain the original context's tone and significance
    - Include all relevant links shared in the conversation
    - If financial strategies are mentioned, highlight them clearly
    - Analyze any data or statistics if they're present and relevant
    - Present information in a structured, easy-to-understand format
    """

    SPECIALIZED_PROMPTS: Dict[str, Dict[str, str]] = {
        'general': {
            'system_prompt': DEFAULT_SYSTEM_PROMPT,
            'user_prompt': DEFAULT_USER_PROMPT
        },
        'defi': {
            'system_prompt': """
            You are a specialized DeFi and crypto analyst focusing on extracting actionable insights
            from cryptocurrency and blockchain-related discussions.

            Analysis Priorities:
            1. Identify yield farming opportunities and stablecoin farming strategies
            2. Assess liquidity provision strategies and risk/reward ratios
            3. Highlight market sentiment and trends across different protocols
            4. Extract APY/APR data and compare different yield options
            5. Note protocol risks, smart contract vulnerabilities, or security concerns
            6. Track important governance decisions or protocol updates
            7. Monitor TVL (Total Value Locked) changes and their implications
            8. Identify arbitrage opportunities or cross-chain strategies
            9. Include all relevant links to protocols, tools, or information sources
            10. Pay special attention to new project launches or token airdrops
            """,
            'user_prompt': """
            Provide a comprehensive analysis of the following crypto/DeFi conversation, 
            emphasizing financial strategies, yield opportunities, and market dynamics.

            Conversation Transcript:
            {text}

            Analysis Requirements:
            - Extract specific financial metrics (APYs, TVL, token prices) with clear sourcing
            - Identify yield farming and stablecoin strategies with their risk levels
            - Highlight arbitrage or market inefficiency opportunities
            - Include all relevant links to protocols, tools, dashboards and resources
            - Note any upcoming protocol launches, airdrops, or major governance votes
            - Summarize sentiment around major DeFi protocols mentioned
            - Analyze any on-chain data or statistics mentioned and their implications
            - Organize information by protocol or strategy type for clarity
            - Prioritize actionable information that can be used for investment decisions
            - DATA IS KEY
            """
        },
        'crypto': {
            'system_prompt': """
            You are a cryptocurrency market analyst specializing in extracting trading insights
            and market intelligence from online discussions.

            Analysis Priorities:
            1. Identify trading setups and technical analysis patterns
            2. Extract price predictions with their supporting rationales
            3. Monitor sentiment around major cryptocurrencies
            4. Track on-chain metrics and their implications (e.g., exchange flows, whale movements)
            5. Note regulatory developments or news that could impact markets
            6. Highlight correlations between crypto and traditional markets
            7. Identify emerging narratives that could drive market cycles
            8. Include all relevant links to charts, data sources, or news articles
            9. Assess macro factors influencing the broader crypto market
            10. Note new token launches or investment opportunities
            """,
            'user_prompt': """
            Analyze the following cryptocurrency conversation for trading insights, 
            market trends, and investment opportunities.

            Conversation Transcript:
            {text}

            Analysis Requirements:
            - Extract specific price levels, support/resistance zones, and technical patterns
            - Identify trading strategies with their timeframes (short/mid/long term)
            - Summarize sentiment around major cryptocurrencies mentioned
            - Include all relevant links to charts, news articles, or analysis tools
            - Highlight on-chain metrics mentioned and their implications
            - Note any macro factors or correlations with traditional markets
            - Identify emerging narratives that could drive price action
            - Organize information by asset or market segment for clarity
            - Prioritize actionable trading or investment information
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
        Dynamically retrieve and customize prompts based on multiple parameters.

        This method provides a sophisticated prompt selection mechanism that:
        - Prioritizes explicit prompt type specification
        - Falls back to topic-based specialized prompts
        - Defaults to general prompts if no specific match is found
        - Allows complete prompt overriding

        Args:
            channel_name (Optional[str]): Context or topic of the conversation.
                Used to select specialized prompts if no explicit type is provided.
            
            prompt_type (Optional[str]): Explicitly specified prompt type.
                Overrides topic-based selection if provided.
            
            override_system_prompt (Optional[str]): Custom system prompt 
                that completely replaces the selected prompt's system prompt.
            
            override_user_prompt (Optional[str]): Custom user prompt 
                that completely replaces the selected prompt's user prompt.

        Returns:
            Dict[str, str]: A dictionary containing 'system_prompt' and 'user_prompt'.
                May include overridden prompts if specified.
        """
        # Determine base prompts with prioritized selection
        if prompt_type and prompt_type in cls.SPECIALIZED_PROMPTS:
            # Explicit prompt type takes highest priority
            prompts = cls.SPECIALIZED_PROMPTS[prompt_type]
        elif channel_name:
            # Try to find specialized prompt based on topic
            topic_lower = channel_name.lower()
            
            # Check for crypto/DeFi related keywords
            if any(term in topic_lower for term in ['defi', 'yield', 'farm', 'staking', 'liquidity', 'lp', 'lending', 'borrowing', 'amm', 'swap', 'stable']):
                prompts = cls.SPECIALIZED_PROMPTS['defi']
            elif any(term in topic_lower for term in ['crypto', 'bitcoin', 'ethereum', 'btc', 'eth', 'token', 'coin', 'trading', 'market', 'airdrop']):
                prompts = cls.SPECIALIZED_PROMPTS['crypto']
            else:
                # Default to general if no match
                prompts = cls.SPECIALIZED_PROMPTS['general']
        else:
            # Fallback to general prompts
            prompts = cls.SPECIALIZED_PROMPTS['general']
        
        # Apply prompt overrides
        if override_system_prompt is not None:
            prompts['system_prompt'] = override_system_prompt
        
        if override_user_prompt is not None:
            prompts['user_prompt'] = override_user_prompt
        
        return prompts

    @classmethod
    def format_user_prompt(
        cls, 
        text: str, 
        channel_name: Optional[str] = None, 
        prompt_type: Optional[str] = None,
        override_system_prompt: Optional[str] = None,
        override_user_prompt: Optional[str] = None
    ) -> str:
        """
        Format the user prompt with the given text and optional customization.

        This method combines text formatting with prompt selection, allowing
        for dynamic and context-aware prompt generation.

        Args:
            text (str): The conversation or text to be summarized.
            
            channel_name (Optional[str]): Context or topic of the conversation.
            
            prompt_type (Optional[str]): Explicitly specified prompt type.
            
            override_system_prompt (Optional[str]): Custom system prompt.
            
            override_user_prompt (Optional[str]): Custom user prompt.

        Returns:
            str: A formatted user prompt ready for LLM submission.
        """
        prompts = cls.get_prompts(
            channel_name=channel_name, 
            prompt_type=prompt_type,
            override_system_prompt=override_system_prompt,
            override_user_prompt=override_user_prompt
        )
        return prompts['user_prompt'].format(text=text)