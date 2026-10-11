"""
Enhanced Utility functions for the Learning Path Generator.
Maintains full backward compatibility with the legacy LangGraph agent signature
while providing robust error handling, MCP tool discovery, and fallback capabilities.
"""

import sys
import os
import asyncio
from typing import Optional, Callable, Any, Dict, List

# Add parent directory to sys.path to enable sharing models and managers
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from prompt import user_goal_prompt

cfg = RunnableConfig(recursion_limit=100)


def initialize_model(google_api_key: str, model_name: str = "gemini-2.5-flash") -> ChatGoogleGenerativeAI:
    """Initialize Google Gemini chat model."""
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=google_api_key,
        temperature=0.3
    )


async def setup_agent_with_tools(
    google_api_key: str,
    youtube_pipedream_url: Optional[str] = None,
    drive_pipedream_url: Optional[str] = None,
    notion_pipedream_url: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None,
    model_name: str = "gemini-2.5-flash"
) -> Any:
    """
    Set up the LangChain/LangGraph agent with MCP tools.
    Gracefully handles optional and unavailable MCP connections.
    """
    try:
        tools_config = {}

        if youtube_pipedream_url and youtube_pipedream_url.strip():
            tools_config["youtube"] = {
                "url": youtube_pipedream_url.strip(),
                "transport": "streamable_http"
            }
            if progress_callback:
                progress_callback("Configuring YouTube MCP integration... ✅")

        if drive_pipedream_url and drive_pipedream_url.strip():
            tools_config["drive"] = {
                "url": drive_pipedream_url.strip(),
                "transport": "streamable_http"
            }
            if progress_callback:
                progress_callback("Configuring Google Drive MCP integration... ✅")

        if notion_pipedream_url and notion_pipedream_url.strip():
            tools_config["notion"] = {
                "url": notion_pipedream_url.strip(),
                "transport": "streamable_http"
            }
            if progress_callback:
                progress_callback("Configuring Notion MCP integration... ✅")

        tools = []
        if tools_config:
            if progress_callback:
                progress_callback("Connecting to MCP servers and discovering tools... 🔄")
            try:
                mcp_client = MultiServerMCPClient(tools_config)
                # Fetch available tools with timeout protection
                tools = await asyncio.wait_for(mcp_client.get_tools(), timeout=10.0)
                if progress_callback:
                    progress_callback(f"Successfully loaded {len(tools)} MCP tool(s)! ✅")
            except Exception as mcp_err:
                if progress_callback:
                    progress_callback(f"Warning: MCP connection issue ({str(mcp_err)}). Continuing with native AI reasoning... ⚠️")
                tools = []
        else:
            if progress_callback:
                progress_callback("Running in Native AI mode (no MCP endpoints configured)... 🤖")

        if progress_callback:
            progress_callback("Creating Gemini agent... ✅")

        model = initialize_model(google_api_key, model_name=model_name)
        agent = create_react_agent(model, tools)

        if progress_callback:
            progress_callback("Setup complete! Generating learning path... 🚀")

        return agent

    except Exception as e:
        print(f"Error in setup_agent_with_tools: {str(e)}")
        raise


def run_agent_sync(
    google_api_key: str,
    youtube_pipedream_url: Optional[str] = None,
    drive_pipedream_url: Optional[str] = None,
    notion_pipedream_url: Optional[str] = None,
    user_goal: str = "",
    progress_callback: Optional[Callable[[str], None]] = None,
    model_name: str = "gemini-2.5-flash"
) -> dict:
    """
    Synchronous wrapper for running the agent.
    Maintains compatibility with original app interface.
    """
    async def _run():
        try:
            agent = await setup_agent_with_tools(
                google_api_key=google_api_key,
                youtube_pipedream_url=youtube_pipedream_url,
                drive_pipedream_url=drive_pipedream_url,
                notion_pipedream_url=notion_pipedream_url,
                progress_callback=progress_callback,
                model_name=model_name
            )

            learning_path_prompt = f"User Goal: {user_goal}\n{user_goal_prompt}"

            if progress_callback:
                progress_callback("Generating your learning path...")

            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=learning_path_prompt)]},
                config=cfg
            )

            if progress_callback:
                progress_callback("Learning path generation complete! 🎉")

            return result
        except Exception as e:
            print(f"Error in _run: {str(e)}")
            raise

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
