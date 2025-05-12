from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from autogen import LLMConfig
from autogen.agentchat import AssistantAgent
from autogen.mcp import create_toolkit
import json
import anyio
import asyncio

# Only needed for Jupyter notebooks
import nest_asyncio
nest_asyncio.apply()

from autogen.agentchat.group import (
    AgentNameTarget,
    AgentTarget,
    AskUserTarget,
    ContextExpression,
    ContextStr,
    ContextStrLLMCondition,
    ContextVariables,
    ExpressionAvailableCondition,
    ExpressionContextCondition,
    GroupChatConfig,
    GroupChatTarget,
    Handoffs,
    NestedChatTarget,
    OnCondition,
    OnContextCondition,
    ReplyResult,
    RevertToUserTarget,
    SpeakerSelectionResult,
    StayTarget,
    StringAvailableCondition,
    StringContextCondition,
    StringLLMCondition,
    TerminateTarget,
)

from autogen.agentchat.group.patterns import (
    DefaultPattern,
    ManualPattern,
    AutoPattern,
    RandomPattern,
    RoundRobinPattern,
)


from autogen import ConversableAgent, UpdateSystemMessage
from autogen.agents.experimental import DocAgent
import copy
from typing import Any, Dict, List
from pydantic import BaseModel, Field


from autogen.agentchat import initiate_group_chat, a_initiate_group_chat

mcp_server_path = Path("mcp_filesystem.py")

# Define the system message for the restaurant selector agent
selector_message = """
You are a restaurant selector agent. Your task is to select the three best eating places in Cambridge for breakfast, lunch, and dinner based on the user's preferences.

You will be given:
1. A list of restaurants in Cambridge with their categories
2. User preferences for food

Select the most appropriate restaurants for each meal based on:
- Matching the user's food preferences
- Restaurant categories and ratings (if available)
- Variety between meals

You must output your selections in a structured format.
""".strip()

# Define the system message for the route planner agent
planner_message = """
You are a route planner agent. Your task is to plan an efficient route between the three selected restaurants in Cambridge.

You will be given:
1. The locations of the three selected restaurants
2. Their geographical coordinates

Plan a route that:
- Minimises travel distance/time
- Is practical for a tourist to follow
- Includes suggestions for transport methods between locations

You must output your route plan in a structured format.
""".strip()

# Define the system message for the companion agent
companion_message = """
You are a friendly travel companion agent. Your task is to present the restaurant selections and route plan to the user in an engaging, conversational manner.

You will be given:
1. Three restaurant selections for breakfast, lunch, and dinner
2. A route plan connecting these restaurants

Present this information in a way that:
- Is engaging and personable
- Highlights the strengths of each restaurant choice
- Makes the route plan clear and easy to follow
- Offers additional insights about Cambridge where relevant

Your tone should be friendly, helpful and conversational.
""".strip()

class RestaurantInfo(BaseModel):
    name: str = Field(..., description="Name of the restaurant")
    type: str = Field(..., description="Type of restaurant (e.g., pub, cafe)")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    
    model_config = {"extra": "forbid"}

class RouteDetails(BaseModel):
    distance: str = Field(..., description="Distance between locations")
    directions: str = Field(..., description="Brief directions between locations")
    
    model_config = {"extra": "forbid"}

class RestaurantSelection(BaseModel):
    breakfast_restaurant: RestaurantInfo = Field(..., description="Details of the selected breakfast restaurant")
    lunch_restaurant: RestaurantInfo = Field(..., description="Details of the selected lunch restaurant")
    dinner_restaurant: RestaurantInfo = Field(..., description="Details of the selected dinner restaurant")
    selection_reasoning: str = Field(..., description="Explanation of why these restaurants were selected based on user preferences")
    
    model_config = {"extra": "forbid"}

class TravelTimes(BaseModel):
    breakfast_to_lunch: str = Field(..., description="Estimated travel time from breakfast to lunch")
    lunch_to_dinner: str = Field(..., description="Estimated travel time from lunch to dinner")
    
    model_config = {"extra": "forbid"}

class RoutePlan(BaseModel):
    route_overview: str = Field(..., description="Brief overview of the full day's route")
    breakfast_to_lunch: RouteDetails = Field(..., description="Route details from breakfast to lunch location")
    lunch_to_dinner: RouteDetails = Field(..., description="Route details from lunch to dinner location")
    transport_recommendations: List[str] = Field(..., description="List of recommended transportation methods")
    travel_times: TravelTimes = Field(..., description="Estimated travel times between locations")
    
    model_config = {"extra": "forbid"}

class CompanionOutput(BaseModel):
    greeting: str = Field(..., description="Friendly greeting to the user")
    day_overview: str = Field(..., description="Overview of the day's eating and travel plan")
    restaurant_highlights: str = Field(..., description="Highlights of each selected restaurant")
    route_guidance: str = Field(..., description="Clear explanation of the route between restaurants")
    closing_remarks: str = Field(..., description="Friendly closing remarks")
    
    model_config = {"extra": "forbid"}
    
    def format(self) -> str:
        return "\n\n".join([
            f"**Hello!** {self.greeting}",
            f"**Your Cambridge Food Day:**\n{self.day_overview}",
            f"**Restaurant Highlights:**\n{self.restaurant_highlights}",
            f"**Getting Around:**\n{self.route_guidance}",
            f"{self.closing_remarks}"
        ])

default_llm_config = {'cache_seed': 42,
                     'temperature': 0.7,
                     'top_p': 0.95,
                     'config_list': [{'model': 'gpt-4o',
                                      'api_key': os.getenv('OPENAI_API_KEY'),
                                      'api_type': 'openai'}],
                     'timeout': 1200}

selector_config = copy.deepcopy(default_llm_config)
selector_config['config_list'][0]['response_format'] = RestaurantSelection

planner_config = copy.deepcopy(default_llm_config)
planner_config['config_list'][0]['response_format'] = RoutePlan

companion_config = copy.deepcopy(default_llm_config)
companion_config['config_list'][0]['response_format'] = CompanionOutput

# Create the three agents
selector_agent = ConversableAgent(
    name="restaurant_selector",
    system_message=selector_message,
    llm_config=selector_config,
    update_agent_state_before_reply=[UpdateSystemMessage(selector_message)],
)

planner_agent = ConversableAgent(
    name="route_planner",
    system_message=planner_message,
    llm_config=planner_config,
    update_agent_state_before_reply=[UpdateSystemMessage(planner_message)],
)

companion_agent = ConversableAgent(
    name="companion",
    system_message=companion_message,
    llm_config=companion_config,
    update_agent_state_before_reply=[UpdateSystemMessage(companion_message)],
)

# Initialize workflow context with default values
workflow_context = ContextVariables(data={
    "restaurant_count": 0,
    "restaurant_categories": [],
    "food_preferences": "casual dining with a mix of traditional British food and international cuisine",
    "restaurants_with_locations": [],
    "selected_restaurants": {
        "breakfast": None,
        "lunch": None,
        "dinner": None
    },
    "route_plan": None
})

async def create_toolkit_and_run(session: ClientSession) -> None:
    # Create a toolkit with available MCP tools
    toolkit = await create_toolkit(session=session)
    
    # First, get data about restaurants in Cambridge
    print("\n--- Getting data about Cambridge restaurants ---")
    
    # 1. Geocode Cambridge
    Cambridge_result = await session.call_tool(
        "geocode_address", 
        {"address": "Cambridge, England"}
    )
    
    # Parse the result
    Cambridge_location = {}
    for content_item in Cambridge_result.content:
        if content_item.type == 'text':
            Cambridge_data = json.loads(content_item.text)
            if isinstance(Cambridge_data, list) and len(Cambridge_data) > 0:
                Cambridge_location = Cambridge_data[0]
            else:
                Cambridge_location = Cambridge_data
            break
    
    if Cambridge_location:
        print(f"Found Cambridge: {Cambridge_location.get('display_name', 'Unknown')}")
        lat = float(Cambridge_location.get('lat', 0))
        lon = float(Cambridge_location.get('lon', 0))
        print(f"Coordinates: {lat}, {lon}")
        
        # 2. Find restaurants nearby
        nearby_result = await session.call_tool(
            "find_nearby_places",
            {
                "latitude": lat,
                "longitude": lon,
                "radius": 2000,  # 2km radius to cover central Cambridge
                "categories": ["amenity"],
                "limit": 1000
            }
        )
        
        # Parse the result
        nearby_places = {}
        for content_item in nearby_result.content:
            if content_item.type == 'text':
                nearby_places = json.loads(content_item.text)
                break
        
        # Get restaurant data
        restaurant_categories = []
        restaurants_with_locations = []
        
        # Filter for food and drink related places
        valid_subcategories = ["restaurant", "pub", "bar", "cafe", "fast_food", "bistro", "food_court"]
        restaurant_count = 0
        categories = nearby_places.get('categories', {})
        
        for category, subcategories in categories.items():
            for subcategory, places in subcategories.items():
                if subcategory.lower() in valid_subcategories:
                    place_count = len(places)
                    restaurant_count += place_count
                    restaurant_categories.append(f"{subcategory}: {place_count} places")
                    # Store detailed information about each restaurant for the selector agent
                    for place in places:
                        # print("place", place)
                        if 'tags' in place and 'name' in place.get('tags', {}):
                            restaurant_info = {
                                'name': place['name'],
                                'type': subcategory,
                                'latitude': place['latitude'],
                                'longitude': place['longitude'],
                                'tags': place.get('tags', {})
                            }
                            restaurants_with_locations.append(restaurant_info)
        
        # Add some debugging output to help understand what we're getting back
        print(f"Total features returned: {nearby_places.get('total_count', 0)}")
        print(f"Categories returned: {list(categories.keys())}")
        if 'amenity' in categories:
            print(f"Amenity subcategories: {list(categories['amenity'].keys())}")
        
        # Update the workflow context with restaurant information
        workflow_context.data["restaurant_count"] = restaurant_count
        workflow_context.data["restaurant_categories"] = restaurant_categories
        workflow_context.data["restaurants_with_locations"] = restaurants_with_locations
        
        print(f"Found {restaurant_count} restaurants in Cambridge")
        print(f"Categories: {restaurant_categories}")
    else:
        print("Could not find Cambridge location data")
    
    # Update the system messages with dynamic data
    selector_system_message = f"""
You are a restaurant selector agent. Your task is to select the three best eating places in Cambridge for breakfast, lunch, and dinner based on the user's preferences.

User food preferences: {{food_preferences}}

You have access to information about {restaurant_count} restaurants in Cambridge:
Categories: {restaurant_categories}

Here is the detailed list of restaurants with their locations:
{{restaurants_with_locations}}

Select the most appropriate restaurants for each meal based on:
- Matching the user's food preferences
- Restaurant categories and other available information
- Variety between meals (breakfast, lunch, dinner)

You must output your selections as a structured response with:
1. Breakfast restaurant details
2. Lunch restaurant details
3. Dinner restaurant details
4. Reasoning for your selections
    """
    
    planner_system_message = """
You are a route planner agent. Your task is to plan an efficient route between the three selected restaurants in Cambridge.

The selected restaurants are:
Breakfast: {selected_restaurants.breakfast}
Lunch: {selected_restaurants.lunch}
Dinner: {selected_restaurants.dinner}

Plan a route that:
- Minimises travel distance/time between locations
- Is practical for a tourist to follow
- Includes suggestions for transport methods (walking, bus, taxi, etc.)

You must output a structured route plan with:
1. Overall route overview
2. Directions from breakfast to lunch
3. Directions from lunch to dinner
4. Transport recommendations
5. Travel times (breakfast_to_lunch and lunch_to_dinner)
    """
    
    companion_system_message = """
You are a friendly travel companion agent. Your task is to present the restaurant selections and route plan to the user in an engaging, conversational manner.

The selected restaurants are:
Breakfast: {selected_restaurants.breakfast}
Lunch: {selected_restaurants.lunch}
Dinner: {selected_restaurants.dinner}

The route plan is:
{route_plan}

Present this information in a way that:
- Is engaging and personable
- Highlights the strengths of each restaurant choice
- Makes the route plan clear and easy to follow
- Offers additional insights about Cambridge where relevant

Your tone should be friendly, helpful and conversational.
    """
    
    # Set up handoffs between agents
    selector_agent.handoffs.set_after_work(AgentTarget(planner_agent))
    planner_agent.handoffs.set_after_work(AgentTarget(companion_agent))
    companion_agent.handoffs.set_after_work(TerminateTarget())
    
    # Define conditions for handoffs
    selector_agent.handoffs.add_llm_conditions([
        OnCondition(
            target=AgentTarget(planner_agent),
            condition=StringLLMCondition(prompt="I have selected the three restaurants and am ready to hand over to the route planner."),
        ),
    ])
    
    planner_agent.handoffs.add_llm_conditions([
        OnCondition(
            target=AgentTarget(companion_agent),
            condition=StringLLMCondition(prompt="I have planned the route and am ready to hand over to the companion agent."),
        ),
    ])
    
    # Define check functions
    def is_restaurant_selection(*args):
        # Can be called with (sender) or (sender, recipient, message)
        if len(args) == 3:  # sender, recipient, message
            sender, recipient, message = args
            return isinstance(message, RestaurantSelection)
        elif len(args) == 1:  # Just sender
            sender = args[0]
            # Can't check message type with just sender, so return False
            return False
        return False
    
    def update_selected_restaurants(*args):
        # Can be called with (sender) or (sender, recipient, message)
        if len(args) == 3:  # sender, recipient, message
            sender, recipient, message = args
            if isinstance(message, RestaurantSelection):
                workflow_context.update({
                    "selected_restaurants": {
                        "breakfast": message.breakfast_restaurant,
                        "lunch": message.lunch_restaurant,
                        "dinner": message.dinner_restaurant
                    }
                })
    
    def is_route_plan(*args):
        # Can be called with (sender) or (sender, recipient, message)
        if len(args) == 3:  # sender, recipient, message
            sender, recipient, message = args
            return isinstance(message, RoutePlan)
        elif len(args) == 1:  # Just sender
            sender = args[0]
            # Can't check message type with just sender, so return False
            return False
        return False
    
    def update_route_plan(*args):
        # Can be called with (sender) or (sender, recipient, message)
        if len(args) == 3:  # sender, recipient, message
            sender, recipient, message = args
            if isinstance(message, RoutePlan):
                workflow_context.update({
                    "route_plan": message
                })
    
    # Set up agent to update context variables after their work
    selector_agent.register_reply(
        [is_restaurant_selection], 
        update_selected_restaurants
    )
    
    planner_agent.register_reply(
        [is_route_plan], 
        update_route_plan
    )

    # Define the agents for the group chat
    agents = [selector_agent, planner_agent, companion_agent]
    
    for agent in agents:
        agent.reset()
    print("All agents reset")

    import shutil
    import os
    
    def delete_cache_folder():
        cache_path = os.path.join(os.getcwd(), ".cache")
        if os.path.isdir(cache_path):
            shutil.rmtree(cache_path)
            print(".cache folder deleted.")
        else:
            print("No .cache folder found in current directory.")
    
    delete_cache_folder()

    # Create the pattern - start with the selector agent directly
    agent_pattern = DefaultPattern(
      agents=agents,
      initial_agent=selector_agent,
      context_variables=workflow_context,
    )
    
    await a_initiate_group_chat(
        pattern=agent_pattern,
        messages="Please select three restaurants for breakfast, lunch, and dinner in Cambridge based on my preference for casual dining with a mix of traditional Hong Kong food and japanese cuisine. Then create a route plan between these places and present the information to me in a friendly, conversational manner.",
        max_rounds=20,
    )


# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="osm-mcp-server",  # The command to run the OSM MCP server
    args=[],  # No additional arguments needed
    env=None
)

async def main():
    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        # Initialize the connection
        await session.initialize()
        await create_toolkit_and_run(session)

if __name__ == "__main__":
    asyncio.run(main())