"""
deploy_agentcore_memory.py

AgentCore Memory Deployment Script
Create Memory for Investment Advisor and save deployment information
"""

import json
import time
import sys
from pathlib import Path
from bedrock_agentcore.memory import MemoryClient

# Add common configuration path
root_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_path))
from config import Config as GlobalConfig

class Config:
    REGION = GlobalConfig.REGION
    MEMORY_NAME = GlobalConfig.MEMORY_NAME

def deploy_memory():
    """Create AgentCore Memory"""
    print("🧠 Creating AgentCore Memory...")
    
    memory_client = MemoryClient(region_name=Config.REGION)
    
    try:
        # Check existing memory
        memories = memory_client.list_memories()
        existing_memory = next((m for m in memories if m['id'].startswith(Config.MEMORY_NAME)), None)
        
        if existing_memory:
            memory_id = existing_memory['id']
            print(f"✅ Using existing memory: {memory_id}")
        else:
            # Create new memory - SUMMARY strategy for Long-term auto-summarization
            from bedrock_agentcore.memory.constants import StrategyType
            
            memory = memory_client.create_memory_and_wait(
                name=Config.MEMORY_NAME,
                description="Investment Advisor - Session-based conversation summary",
                strategies=[
                    {
                        StrategyType.SUMMARY.value: {
                            "name": "InvestmentSessionSummary",
                            "description": "Auto-summarizes entire investment consultation session",
                            "namespaces": ["investment/session/{sessionId}"]
                        }
                    }
                ],
                event_expiry_days=7,   # Short-term retention period
                max_wait=300,
                poll_interval=10
            )
            memory_id = memory['id']
            print(f"✅ New memory created: {memory_id}")
        
        return memory_id
        
    except Exception as e:
        print(f"❌ Memory creation failed: {e}")
        raise

def save_deployment_info(memory_id):
    """Save deployment information"""
    deployment_info = {
        "memory_id": memory_id,
        "memory_name": Config.MEMORY_NAME,
        "region": Config.REGION,
        "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    info_file = Path(__file__).parent / "deployment_info.json"
    with open(info_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    return str(info_file)

def main():
    try:
        print("🧠 AgentCore Memory Deployment Started")
        
        # Create Memory
        memory_id = deploy_memory()
        
        # Save deployment information
        info_file = save_deployment_info(memory_id)
        
        print(f"\n🎉 Deployment Complete!")
        print(f"📄 Deployment Info: {info_file}")
        print(f"🧠 Memory ID: {memory_id}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Deployment Failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())