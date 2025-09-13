"""
deploy_mcp.py

MCP Server Deployment Script
Deploy MCP Server for ETF data retrieval
"""

import boto3
import sys
import time
import json
from pathlib import Path
from bedrock_agentcore_starter_toolkit import Runtime

# Add common configuration and shared module paths
root_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_path))
sys.path.insert(0, str(root_path / "shared"))

from config import Config as GlobalConfig
from cognito_utils import get_or_create_user_pool, get_or_create_resource_server, get_or_create_m2m_client
from runtime_utils import create_agentcore_runtime_role

class Config:
    """MCP Server deployment configuration"""
    REGION = GlobalConfig.REGION
    MCP_SERVER_NAME = GlobalConfig.MCP_SERVER_NAME

def setup_cognito_auth():
    """Set up Cognito authentication"""
    print("🔐 Setting up Cognito authentication...")
    cognito = boto3.client('cognito-idp', region_name=Config.REGION)
    
    # Create/get User Pool
    user_pool_id = get_or_create_user_pool(cognito, f"{Config.MCP_SERVER_NAME}-pool", Config.REGION)
    
    # Create/get Resource Server
    resource_server_id = f"{Config.MCP_SERVER_NAME}-server"
    scopes = [
        {"ScopeName": "runtime:read", "ScopeDescription": "Runtime read access"},
        {"ScopeName": "runtime:write", "ScopeDescription": "Runtime write access"}
    ]
    get_or_create_resource_server(cognito, user_pool_id, resource_server_id, 
                                 f"{Config.MCP_SERVER_NAME} Resource Server", scopes)
    
    # Create/get M2M Client
    client_id, client_secret = get_or_create_m2m_client(
        cognito, user_pool_id, f"{Config.MCP_SERVER_NAME}-client", 
        resource_server_id, ["runtime:read", "runtime:write"]
    )
    
    discovery_url = f'https://cognito-idp.{Config.REGION}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration'
    
    return {
        'user_pool_id': user_pool_id,
        'client_id': client_id,
        'client_secret': client_secret,
        'discovery_url': discovery_url
    }

def create_mcp_runtime(role_arn, auth_components):
    """Create MCP Server Runtime"""
    print("🔧 Configuring MCP Server Runtime...")
    current_dir = Path(__file__).parent
    
    auth_config = {
        "customJWTAuthorizer": {
            "allowedClients": [auth_components['client_id']],
            "discoveryUrl": auth_components['discovery_url'],
        }
    }
    
    runtime = Runtime()
    runtime.configure(
        entrypoint=str(current_dir / "server.py"),
        execution_role=role_arn,
        auto_create_ecr=True,
        requirements_file=str(current_dir / "requirements.txt"),
        region=Config.REGION,
        authorizer_configuration=auth_config,
        protocol="MCP",
        agent_name=Config.MCP_SERVER_NAME
    )
    
    # Execute deployment
    launch_result = runtime.launch()
    
    # Wait for deployment completion
    for i in range(30):  # Maximum 15 minutes wait
        try:
            status = runtime.status().endpoint['status']
            print(f"📊 Status: {status} ({i*30} seconds elapsed)")
            if status in ['READY', 'CREATE_FAILED', 'DELETE_FAILED', 'UPDATE_FAILED']:
                break
        except Exception as e:
            print(f"⚠️ Status check error: {e}")
        time.sleep(30)
    
    if status != 'READY':
        raise Exception(f"MCP Server deployment failed: {status}")
    
    return {
        'agent_arn': launch_result.agent_arn,
        'agent_id': launch_result.agent_id
    }

def save_deployment_info(result):
    """Save deployment information"""
    info_file = Path(__file__).parent / "mcp_deployment_info.json"
    with open(info_file, 'w') as f:
        json.dump(result, f, indent=2)
    return str(info_file)

def main():
    try:
        print("🚀 ETF Data MCP Server Deployment")
        
        # Create IAM role
        iam_role = create_agentcore_runtime_role(Config.MCP_SERVER_NAME, Config.REGION)
        iam_role_name = iam_role['Role']['RoleName']
        time.sleep(10)  # Wait for IAM propagation
        
        # Set up Cognito authentication
        auth_components = setup_cognito_auth()
        
        # Create MCP Server Runtime
        runtime_result = create_mcp_runtime(iam_role['Role']['Arn'], auth_components)
        
        # Extract ECR repository name
        ecr_repo_name = None
        if hasattr(runtime_result, 'ecr_uri') and runtime_result['ecr_uri']:
            ecr_repo_name = runtime_result['ecr_uri'].split('/')[-1].split(':')[0]

        # Configure deployment result
        result = {
            'agent_arn': runtime_result['agent_arn'],
            'agent_id': runtime_result['agent_id'],
            'user_pool_id': auth_components['user_pool_id'],
            'client_id': auth_components['client_id'],
            'client_secret': auth_components['client_secret'],
            'region': Config.REGION,
            'iam_role_name': iam_role_name,
            'ecr_repo_name': ecr_repo_name,
            'deployed_at': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save deployment information
        info_file = save_deployment_info(result)
        
        print(f"\n🎉 MCP Server Deployment Complete!")
        print(f"🔗 Agent ARN: {result['agent_arn']}")
        print(f"📄 Deployment Info: {info_file}")
        
        return result
        
    except Exception as e:
        print(f"❌ MCP Server Deployment Failed: {e}")
        raise

if __name__ == "__main__":
    main()