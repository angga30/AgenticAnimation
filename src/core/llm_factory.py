import os
from langchain_core.language_models.chat_models import BaseChatModel

def get_llm(temperature: float = 0.7) -> BaseChatModel:
    """
    Factory function to get the configured LLM.
    Supports switching between OpenAI, Google GenAI, etc., based on environment variables.
    This ensures the platform is LLM-agnostic.
    """
    llm_provider = os.environ.get("LLM_PROVIDER", "openai").lower()

    if llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            temperature=temperature
        )
    elif llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=os.environ.get("GOOGLE_MODEL", "gemini-1.5-pro"),
            temperature=temperature
        )
    elif llm_provider == "ollama":
        # For local models
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=os.environ.get("OLLAMA_MODEL", "llama3"),
            temperature=temperature
        )
    elif llm_provider == "qwen":
        # Alibaba DashScope (Qwen)
        from langchain_community.chat_models.tongyi import ChatTongyi
        return ChatTongyi(
            dashscope_api_key=os.environ.get("DASHSCOPE_API_KEY"),
            model=os.environ.get("QWEN_MODEL", "qwen-max"),
            temperature=temperature
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_provider}")

def get_vision_llm(temperature: float = 0.2) -> BaseChatModel:
    """
    Returns a model capable of processing images.
    """
    llm_provider = os.environ.get("LLM_PROVIDER", "openai").lower()

    if llm_provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.environ.get("OPENAI_VISION_MODEL", "gpt-4o"),
            temperature=temperature
        )
    elif llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=os.environ.get("GOOGLE_VISION_MODEL", "gemini-1.5-flash"),
            temperature=temperature
        )
    elif llm_provider == "qwen":
        from langchain_community.chat_models.tongyi import ChatTongyi
        # DashScope deprecated Qwen2-VL, current stable vision model is qwen-vl-max or qwen-vl-plus
        return ChatTongyi(
            dashscope_api_key=os.environ.get("DASHSCOPE_API_KEY"),
            model=os.environ.get("QWEN_VISION_MODEL", "qwen3.5-omni-plus"),
            temperature=temperature
        )
    else:
        raise ValueError(f"LLM Provider '{llm_provider}' does not support vision capabilities for get_vision_llm(). Please use 'openai', 'google', or 'qwen'.")
