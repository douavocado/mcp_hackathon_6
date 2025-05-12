# Cambridge Restaurant Planner

A multi-agent system using AutoGen and OpenStreetMap MCP to plan a day of dining in Cambridge, with restaurant selection, route planning, and companion guidance.

## Project Structure

The project is organized into the following modules:

- `main.py` - Entry point for the application
- `models.py` - Pydantic models for structured data
- `agent_messages.py` - System messages for each agent
- `agents.py` - Agent definitions and configurations
- `workflow.py` - Workflow logic and context management
- `location_getter.py` - Original monolithic implementation (kept for reference)

## Requirements

- Python 3.9+
- AutoGen
- MCP Client
- OpenStreetMap MCP Server

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - Create a `.env` file with your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

3. Install the OSM MCP server:
   ```bash
   ./installer.sh
   ```

## Running the Application

To run the application:

```bash
python main.py
```

This will:
1. Connect to the OSM MCP server
2. Create the necessary agents
3. Retrieve restaurant data for Cambridge
4. Run the agent workflow to select restaurants, plan a route, and present the plan

## Customization

You can customize the food preferences by modifying the `food_preferences` field in the workflow context (in `workflow.py`), or by passing a different initial message to the `run_restaurant_workflow` function.

# Calendar Agent for Restaurant Planning

## Overview

This implementation adds a calendar agent to the Cambridge restaurant planning system. The calendar agent reads calendar entries from a file and extracts location information. It then uses the OpenStreetMap MCP (Machine Conversation Protocol) to geocode these locations, obtaining latitude and longitude coordinates.

## Files

- `calendar_agent.py`: Core implementation of the calendar agent
- `calendar/example_calendar.md`: Example calendar entries in Markdown format
- `workflow.py`: Updated workflow to integrate the calendar agent
- `agent_messages.py`: Updated message templates for agents

## Calendar Agent Features

- Parses calendar entries from a Markdown file
- Extracts location information using regex patterns
- Uses OpenStreetMap MCP to geocode locations
- Returns structured location data with coordinates
- Provides error handling for various failure cases

## Integration with Workflow

The calendar agent has been integrated into the main workflow:

1. The workflow calls `process_calendar_data()` to process calendar entries
2. Location data is added to the workflow context
3. The selector and planner agents use this data to optimize restaurant selections and route planning

## Example Calendar Entries

The system can extract locations from entries like:

```
17:30 - 18:30    Dentist Appointment at Cambridge Dental
20:00 - 21:30    Pub Quiz at The Crown & Anchor
```

## Testing

You can test the basic functionality with:

```
python calendar_agent.py
```

For full functionality with geocoding, the agent should be used within the main workflow with an active MCP session.

## Future Improvements

- Support for more calendar formats
- Better location extraction using NLP
- Handling of recurring events
- Integration with actual calendar services (Google Calendar, etc.)
