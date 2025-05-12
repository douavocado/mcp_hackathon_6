"""
Calendar agent implementation for the Cambridge restaurant planning system.
This agent processes calendar entries to extract location information and uses 
OpenStreetMap MCP to geocode the locations.
"""

import os
import json
import re
import asyncio
from typing import Any, Optional, List, Dict, Tuple
from datetime import datetime, time

from autogen import ConversableAgent, Agent, OpenAIWrapper
from mcp import ClientSession

from models import Geolocation


def parse_calendar_entries(calendar_file_path: str) -> List[Dict[str, Any]]:
    """
    Parse calendar entries from a markdown file.
    
    Args:
        calendar_file_path: Path to the calendar file
        
    Returns:
        List of calendar entries with time and description
    """
    entries = []
    
    with open(calendar_file_path, 'r') as f:
        lines = f.readlines()
    
    # Skip header lines (first line with # and empty lines)
    data_lines = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
    
    for line in data_lines:
        # Extract time range and description
        time_match = re.match(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s+(.*)', line)
        if time_match:
            start_time, end_time, description = time_match.groups()
            entries.append({
                "start_time": start_time,
                "end_time": end_time,
                "description": description.strip()
            })
    
    return entries


def extract_location_from_description(description: str) -> Optional[str]:
    """
    Extract location details from a calendar entry description.
    
    Args:
        description: Calendar entry description
        
    Returns:
        Location string if found, None otherwise
    """
    # Skip general activities that aren't likely to have meaningful locations
    skip_terms = [
        "breakfast", "lunch", "dinner", "coffee break", "meeting", "call", "run", 
        "phone call", "zoom", "online", "virtual"
    ]
    
    # Check if the description is likely a generic activity
    lower_desc = description.lower()
    for term in skip_terms:
        if term in lower_desc and "at " not in lower_desc and "in " not in lower_desc:
            return None
    
    # Common location patterns
    at_pattern = r'at\s+([A-Za-z0-9\s&\']+(?:\s*,\s*[A-Za-z0-9\s&\']+)*)'
    in_pattern = r'in\s+([A-Za-z0-9\s&\']+(?:\s*,\s*[A-Za-z0-9\s&\']+)*)'
    
    # Check for "at Location" pattern
    at_match = re.search(at_pattern, description)
    if at_match:
        return at_match.group(1).strip()
    
    # Check for "in Location" pattern
    in_match = re.search(in_pattern, description)
    if in_match:
        return in_match.group(1).strip()
    
    # For events with no preposition, check if it includes venue-like terms
    venue_terms = ["pub", "restaurant", "café", "cafe", "bar", "hotel", "office", "center", "centre"]
    words = description.split()
    for word in words:
        lower_word = word.lower()
        if any(term in lower_word for term in venue_terms):
            return description
    
    # If the entry has specific formatting like "Event Name @ Venue"
    if "@" in description:
        parts = description.split("@")
        if len(parts) > 1:
            return parts[1].strip()
    
    return None


async def geocode_location(location: str, session: ClientSession) -> Optional[Dict[str, Any]]:
    """
    Geocode a location string using the OpenStreetMap MCP.
    
    Args:
        location: Location string to geocode
        session: MCP client session
        
    Returns:
        Location information with coordinates if found, None otherwise
    """
    try:
        # If location has "Cambridge" in it, use as is
        query = location if "Cambridge" in location else f"{location}, Cambridge, England"
        # Call the geocode_address tool
        result = await session.call_tool(
            "geocode_address", 
            {"address": query}
        )
        
        
        # Parse the JSON response from the text content
        for content_item in result.content:
            if content_item.type == 'text':
                locations = json.loads(content_item.text)
                
                # Return the first match if available
                if isinstance(locations, list) and len(locations) > 0:
                    return locations[0]
                elif isinstance(locations, dict):
                    return locations
        
        return None
    
    except Exception as e:
        print(f"Error geocoding location '{location}': {str(e)}")
        return None


def create_calendar_agent(mcp_session: ClientSession = None):
    """
    Create a calendar agent that processes calendar entries and returns location information.
    
    Args:
        mcp_session: MCP client session for geocoding
        
    Returns:
        ConversableAgent configured for calendar processing
    """
    agent = ConversableAgent(
        name="calendar",
        system_message="""
        You are a calendar agent. Your task is to find the location inferred by entries of a calendar 
        and return the latitude and longitude of the location.
        
        You will be given:
        1. A list of entries of a calendar
        
        You must output the latitude and longitude of the location inferred by the entries of the calendar.
        Not every entry of the calendar will be relevant to the location, so you must ignore the irrelevant entries.
        
        You must output your answer in a structured format, in a report of where the user is likely to be at what times in the day.
        """.strip()
    )
    
    # Store the MCP session on the agent
    agent._mcp_session = mcp_session
    
    # Add the process calendar entries reply function
    async def process_calendar_entries(
        agent: ConversableAgent,
        messages: Optional[List[Dict[str, Any]]] = None,
        sender: Optional[Agent] = None,
        config: Optional[OpenAIWrapper] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        # Default calendar file path
        calendar_file_path = os.path.join(os.getcwd(), "calendar", "example_calendar.md")
        
        # Parse the calendar entries
        try:
            entries = parse_calendar_entries(calendar_file_path)
            if not entries:
                return True, {
                    "content": "No calendar entries found. Please check the calendar file."
                }
        except Exception as e:
            return True, {
                "content": f"Error parsing calendar file: {str(e)}"
            }
        
        # Process each entry to find locations
        location_entries = []
        
        for entry in entries:
            location = extract_location_from_description(entry["description"])
            
            if location:
                # Get the coordinates for this location
                location_info = None
                if agent._mcp_session:
                    try:
                        location_info = await geocode_location(location, agent._mcp_session)
                    except Exception as e:
                        print(f"Error geocoding location '{location}': {str(e)}")
                
                if location_info and "lat" in location_info and "lon" in location_info:
                    lat = float(location_info["lat"])
                    lon = float(location_info["lon"])
                    
                    location_entries.append({
                        "time": f"{entry['start_time']} - {entry['end_time']}",
                        "description": entry["description"],
                        "location": location,
                        "display_name": location_info.get("name", location),
                        "latitude": lat,
                        "longitude": lon
                    })
        
        # Format the response
        if location_entries:
            report_lines = ["Report of user locations based on calendar entries:"]
            
            for entry in location_entries:
                report_lines.append(
                    f"- User is likely to be at {entry['display_name']} at {entry['time']}"
                )
            
            # Create a structured Geolocation object for each location
            locations = [
                Geolocation(latitude=entry["latitude"], longitude=entry["longitude"])
                for entry in location_entries
            ]
            
            # Return the full report and the structured data
            return True, {
                "content": "\n".join(report_lines),
                "locations": locations,  # Additional structured data
                "location_entries": location_entries  # Full location entries with time info
            }
        else:
            if agent._mcp_session:
                return True, {
                    "content": "Found calendar entries but could not identify any specific locations with coordinates."
                }
            else:
                return True, {
                    "content": "No MCP session available for geocoding. Please initialize the agent with an MCP session."
                }
    
    # Register our reply function with the agent
    agent.register_reply(
        trigger=[Agent, None],
        reply_func=process_calendar_entries
    )
    
    return agent


async def test_calendar_agent():
    """Test function to demonstrate the calendar agent's capabilities."""
    import asyncio
    
    # Parse the calendar entries directly
    calendar_file_path = os.path.join(os.getcwd(), "calendar", "example_calendar.md")
    entries = parse_calendar_entries(calendar_file_path)
    
    print("Calendar entries found:")
    for entry in entries:
        print(f"- {entry['start_time']} to {entry['end_time']}: {entry['description']}")
    
    print("\nExtracted locations:")
    for entry in entries:
        location = extract_location_from_description(entry['description'])
        if location:
            print(f"- From '{entry['description']}': Found location '{location}'")
        else:
            print(f"- From '{entry['description']}': No location found")
    
    print("\nNote: For complete functionality with geocoding,")
    print("this agent should be used within the main workflow with an active MCP session.")


if __name__ == "__main__":
    # Run the test function
    asyncio.run(test_calendar_agent()) 