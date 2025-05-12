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
