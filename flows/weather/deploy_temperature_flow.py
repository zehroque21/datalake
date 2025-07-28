"""
Auto-deploy script for Campinas Temperature Pipeline
This script automatically deploys and schedules the temperature monitoring flow
"""

import asyncio
from prefect import serve
from prefect.client.schemas.schedules import IntervalSchedule
from datetime import timedelta
import sys
import os

# Add the flows directory to Python path
sys.path.append('/app/flows')

from weather.campinas_temperature import campinas_temperature_pipeline


async def deploy_temperature_flow():
    """Deploy the temperature monitoring flow with automatic scheduling"""
    print("🚀 Deploying Campinas Temperature Pipeline...")
    
    try:
        # Create a deployment with automatic scheduling
        deployment = await campinas_temperature_pipeline.to_deployment(
            name="campinas-temperature-monitor",
            description="Automated temperature monitoring for Campinas, SP",
            tags=["weather", "campinas", "temperature", "monitoring"],
            
            # Schedule to run every 30 minutes
            schedule=IntervalSchedule(interval=timedelta(minutes=30)),
            
            # Flow configuration
            parameters={},
            
            # Work pool configuration (local for Docker)
            work_pool_name="default-agent-pool",
            
            # Deployment settings
            is_schedule_active=True,
        )
        
        print("✅ Temperature pipeline deployment created successfully!")
        print(f"   📅 Schedule: Every 30 minutes")
        print(f"   🏷️ Tags: {deployment.tags}")
        print(f"   📝 Description: {deployment.description}")
        
        # Serve the deployment
        print("🔄 Starting deployment server...")
        await serve(
            deployment,
            webserver=False,  # Don't start additional webserver
            limit=1  # Process one flow run at a time
        )
        
    except Exception as e:
        print(f"❌ Error deploying temperature flow: {e}")
        raise


if __name__ == "__main__":
    print("🌡️ Auto-deploying Campinas Temperature Monitor...")
    asyncio.run(deploy_temperature_flow())

