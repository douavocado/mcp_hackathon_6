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

def get_user_food_preferences():
    """Collect food preferences from the user."""
    print("\n--- Cambridge Restaurant Planner ---")
    print("Please tell us about your food preferences.")
    default_preferences = "casual dining with a mix of traditional British food and international cuisine"
    user_input = input(f"Food preferences [{default_preferences}]: ").strip()
    
    # If user doesn't input anything, use the default
    if not user_input:
        return default_preferences
    return user_input

def get_user_constraints():
    """Collect any constraints from the user."""
    print("\nDo you have any dietary restrictions or other constraints?")
    default_constraints = "no specific constraints"
    user_input = input(f"Constraints [{default_constraints}]: ").strip()
    
    # If user doesn't input anything, use the default
    if not user_input:
        return default_constraints
    return user_input

def get_requested_meals():
    """Ask the user which meals they want recommendations for."""
    print("\nWhich meals would you like recommendations for?")
    print("1. Breakfast")
    print("2. Lunch")
    print("3. Dinner")
    print("4. All meals")
    
    valid_response = False
    requested_meals = []
    
    while not valid_response:
        user_input = input("Enter the numbers of your choices (e.g., '1,3' for breakfast and dinner): ").strip()
        
        # Default to all meals if no input
        if not user_input:
            return ["breakfast", "lunch", "dinner"]
        
        # Process input
        try:
            choices = [int(choice.strip()) for choice in user_input.split(',')]
            valid_response = True
            
            # Process each choice
            for choice in choices:
                if choice == 1 and "breakfast" not in requested_meals:
                    requested_meals.append("breakfast")
                elif choice == 2 and "lunch" not in requested_meals:
                    requested_meals.append("lunch")
                elif choice == 3 and "dinner" not in requested_meals:
                    requested_meals.append("dinner")
                elif choice == 4:
                    requested_meals = ["breakfast", "lunch", "dinner"]
                    break
                else:
                    print(f"Invalid choice: {choice}. Please try again.")
                    valid_response = False
                    requested_meals = []
                    break
            
            # Ensure at least one meal is selected
            if len(requested_meals) == 0:
                print("You must select at least one meal. Please try again.")
                valid_response = False
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas.")
            valid_response = False
    
    return requested_meals

async def main():
    """Main entry point for the application."""
    print("Starting Cambridge Restaurant Planner...")
    
    # Get user's food preferences and constraints
    food_preferences = get_user_food_preferences()
    constraints = get_user_constraints()
    requested_meals = get_requested_meals()
    
    # Connect to the MCP server
    async with stdio_client(SERVER_PARAMS) as (read, write), ClientSession(read, write) as session:
        # Initialize the connection
        await session.initialize()
        print("Connected to OSM MCP server")
        
        # Create the agents
        agents = create_agents()
        print("Created all agents")
        
        # Create a comma-separated string of requested meals for the initial message
        meals_str = ", ".join(requested_meals)
        
        # Create the initial message with the user's food preferences and constraints
        initial_message = f"Please select restaurants for {meals_str} in Cambridge based on my food preference for {food_preferences} and my constraints: {constraints}. Then create a route plan between these places and present the information to me in a friendly, conversational manner."
        
        # Run the restaurant planning workflow
        result = await run_restaurant_workflow(
            session=session, 
            agents=agents,
            initial_message=initial_message,
            user_food_preferences=food_preferences,
            user_constraints=constraints,
            requested_meals=requested_meals
        )
        
        print("\nWorkflow completed!")
        return result

if __name__ == "__main__":
    asyncio.run(main()) 