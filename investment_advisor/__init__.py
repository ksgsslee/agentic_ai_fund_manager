"""
Investment Advisor Orchestrator Package

LangGraph-based Multi-Agent Investment Advisory System.
Implements sequential workflow pattern where specialized agents collaborate
in a defined order: Financial Analyst → Portfolio Architect → Risk Manager.

This orchestrator leverages:
- LangGraph for workflow orchestration and state management
- AWS Bedrock AgentCore for agent runtime and memory
- Sequential agent collaboration with shared state
- Long-term memory with automatic session summarization
"""

__version__ = "1.0.0"
__author__ = "Investment Advisor Team"
__description__ = "LangGraph Multi-Agent Investment Advisory System with Sequential Workflow"