"""
Cambridge Restaurant Planner - Entry Point

This script serves as the main entry point for the Cambridge restaurant planning application.
It connects to the OSM MCP server, creates the necessary agents, and runs the planning workflow.
"""

import asyncio
import os
from dotenv import load_dotenv

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

from agents import create_agents
from workflow import run_restaurant_workflow

# Load environment variables
load_dotenv()

# Create server parameters for stdio connection
SERVER_PARAMS = StdioServerParameters(
    command="osm-mcp-server",  # The command to run the OSM MCP server
    args=[],  # No additional arguments needed
    env=None
)

async def main():
    """Main entry point for the application."""
    print("Starting Cambridge Restaurant Planner...")
    
    # Connect to the MCP server
    async with stdio_client(SERVER_PARAMS) as (read, write), ClientSession(read, write) as session:
        # Initialize the connection
        await session.initialize()
        print("Connected to OSM MCP server")
        
        # Create the agents
        agents = create_agents()
        print("Created all agents")
        
        # Run the restaurant planning workflow
        result = await run_restaurant_workflow(
            session=session, 
            agents=agents,
            initial_message="Please select three restaurants for breakfast, lunch, and dinner in Cambridge based on my food preference for casual dining with a mix of traditional British food and international cuisine. Then create a route plan between these places and present the information to me in a friendly, conversational manner."
        )
        
        print("\nWorkflow completed!")
        return result

if __name__ == "__main__":
    asyncio.run(main()) 