"""
Workflow logic for the Cambridge restaurant planning system.
Includes context management, workflow steps, and agent coordination.
"""

import json
import shutil
import os
from typing import Dict, Any, List, Set

from autogen.agentchat.group import ContextVariables
from autogen.agentchat.group.patterns import DefaultPattern
from autogen.agentchat import a_initiate_group_chat
from models import RestaurantSelection, RoutePlan
from mcp import ClientSession
from agent_messages import DYNAMIC_SELECTOR_MESSAGE, DYNAMIC_PLANNER_MESSAGE, DYNAMIC_COMPANION_MESSAGE

def init_workflow_context() -> ContextVariables:
    """Initialize the workflow context with default values."""
    return ContextVariables(data={
        "restaurant_count": 0,
        "restaurant_categories": [],
        "food_preferences": "None",
        "constraints": "None",
        "requested_meals": ["breakfast", "lunch", "dinner"],  # Default to all meals
        "restaurants_with_locations": [],
        "selected_restaurants": {},
        "route_plan": None
    })

def setup_context_handlers(selector_agent, planner_agent, companion_agent, workflow_context: ContextVariables):
    """Set up handlers to update the context when agents produce outputs."""
    
    # Helper function to format restaurant details for messages
    def format_restaurant_details(selected_restaurants):
        details = []
        for meal, restaurant in selected_restaurants.items():
            if restaurant:
                details.append(f"{meal.capitalize()}: {restaurant.name} (Type: {restaurant.type})")
        return "\n".join(details)
    
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
                selected_restaurants = {}
                # Only add restaurants for the requested meals
                if "breakfast" in message.selected_meals and message.breakfast_restaurant:
                    selected_restaurants["breakfast"] = message.breakfast_restaurant
                if "lunch" in message.selected_meals and message.lunch_restaurant:
                    selected_restaurants["lunch"] = message.lunch_restaurant
                if "dinner" in message.selected_meals and message.dinner_restaurant:
                    selected_restaurants["dinner"] = message.dinner_restaurant
                
                workflow_context.update({
                    "selected_restaurants": selected_restaurants,
                    "selected_meals": message.selected_meals
                })
                
                # Update the planner agent's system message with the selected restaurants
                planner_system_message = DYNAMIC_PLANNER_MESSAGE.format(
                    selected_meals=", ".join(message.selected_meals),
                    restaurant_details=format_restaurant_details(selected_restaurants)
                )
                planner_agent.update_system_message(planner_system_message)
    
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
                
                # Update the companion agent's system message with the route plan
                companion_system_message = DYNAMIC_COMPANION_MESSAGE.format(
                    selected_meals=", ".join(message.selected_meals),
                    restaurant_details=format_restaurant_details(workflow_context.get("selected_restaurants", {})),
                    route_plan=message
                )
                companion_agent.update_system_message(companion_system_message)
    
    # Set up agent to update context variables after their work
    selector_agent.register_reply(
        [is_restaurant_selection], 
        update_selected_restaurants
    )
    
    planner_agent.register_reply(
        [is_route_plan], 
        update_route_plan
    )

async def get_cambridge_restaurant_data(session: ClientSession, workflow_context: ContextVariables) -> None:
    """
    Get data about restaurants in Cambridge using the MCP toolkit.
    Updates the workflow context with the retrieved data.
    """
    print("\n--- Getting data about Cambridge restaurants ---")
    
    # 1. Geocode Cambridge
    cambridge_result = await session.call_tool(
        "geocode_address", 
        {"address": "Cambridge, England"}
    )
    
    # Parse the result
    cambridge_location = {}
    for content_item in cambridge_result.content:
        if content_item.type == 'text':
            cambridge_data = json.loads(content_item.text)
            if isinstance(cambridge_data, list) and len(cambridge_data) > 0:
                cambridge_location = cambridge_data[0]
            else:
                cambridge_location = cambridge_data
            break
    
    if cambridge_location:
        print(f"Found Cambridge: {cambridge_location.get('display_name', 'Unknown')}")
        lat = float(cambridge_location.get('lat', 0))
        lon = float(cambridge_location.get('lon', 0))
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
                        if 'tags' in place and 'name' in place.get('tags', {}):
                            restaurant_info = {
                                'name': place['tags'].get('name', 'Unknown Restaurant'),
                                'type': subcategory,
                                'latitude': place['latitude'],
                                'longitude': place['longitude'],
                                'tags': place.get('tags', {})
                            }
                            restaurants_with_locations.append(restaurant_info)
        
        # Add some debugging output to help understand what we're getting back
        print(f"Total features returned: {nearby_places.get('total_count', 0)}")
        print(f"Categories returned: {list(categories.keys())}")
        
        # Update the workflow context with restaurant information
        workflow_context.update({
            "restaurant_count": restaurant_count,
            "restaurant_categories": restaurant_categories,
            "restaurants_with_locations": restaurants_with_locations
        })
        
        print(f"Found {restaurant_count} restaurants in Cambridge")
    else:
        print("Could not find Cambridge location data")

def clear_cache():
    """Delete the .cache folder if it exists."""
    cache_path = os.path.join(os.getcwd(), ".cache")
    if os.path.isdir(cache_path):
        shutil.rmtree(cache_path)
        print(".cache folder deleted.")
    else:
        print("No .cache folder found in current directory.")

async def run_restaurant_workflow(session: ClientSession, agents, initial_message: str = None, 
                                  user_food_preferences: str = None, user_constraints: str = None,
                                  requested_meals: List[str] = None):
    """Run the full restaurant recommendation workflow."""
    selector_agent, planner_agent, companion_agent = agents
    
    # Reset agents
    for agent in [selector_agent, planner_agent, companion_agent]:
        agent.reset()
    print("All agents reset")
    
    # Clear the cache
    clear_cache()
    
    # Initialize the workflow context
    workflow_context = init_workflow_context()
    
    # Update context with user preferences, constraints, and requested meals
    context_updates = {}
    if user_food_preferences:
        context_updates["food_preferences"] = user_food_preferences
    if user_constraints:
        context_updates["constraints"] = user_constraints
    if requested_meals:
        print(f"Requested meals: {requested_meals}")
        context_updates["requested_meals"] = requested_meals
    
    if context_updates:
        workflow_context.update(context_updates)
    
    # Get restaurant data from Cambridge
    await get_cambridge_restaurant_data(session, workflow_context)
    
    # Set up context update handlers
    setup_context_handlers(selector_agent, planner_agent, companion_agent, workflow_context)
    
    # Update selector message
    print(workflow_context.get("requested_meals"), type(workflow_context.get("requested_meals")))
    selector_system_message = DYNAMIC_SELECTOR_MESSAGE.format(
        food_preferences=workflow_context.get("food_preferences"),
        constraints=workflow_context.get("constraints"),
        requested_meals=", ".join(workflow_context.get("requested_meals")),
        restaurant_count=workflow_context.get("restaurant_count"),
        restaurant_categories="\n".join(workflow_context.get("restaurant_categories", [])),
        restaurants_with_locations=json.dumps(workflow_context.get("restaurants_with_locations"), indent=2,)
    )
    selector_agent.update_system_message(selector_system_message)
    
    # Create the agent pattern
    agent_pattern = DefaultPattern(
        agents=[selector_agent, planner_agent, companion_agent],
        initial_agent=selector_agent,
        context_variables=workflow_context,
    )
    
    # Default message if none provided
    if not initial_message:
        meals_str = ", ".join(workflow_context.get("requested_meals"))
        initial_message = f"Please select restaurants for {meals_str} in Cambridge based on my food preference for {workflow_context.get('food_preferences')} and my constraints: {workflow_context.get('constraints')}. Then create a route plan between these places and present the information to me in a friendly, conversational manner."
    
    # Run the group chat
    result = await a_initiate_group_chat(
        pattern=agent_pattern,
        messages=initial_message,
        max_rounds=20,
    )
    
    return result 