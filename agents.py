"""
Agent definitions for the Cambridge restaurant system.
Includes agent configurations, LLM settings, and agent creation functions.
"""

import os
import copy
from dotenv import load_dotenv
from autogen import ConversableAgent, UpdateSystemMessage
from autogen.agentchat.group import AgentTarget, TerminateTarget

# Import models and messages
from models import RestaurantSelection, RoutePlan, CompanionOutput
from agent_messages import SELECTOR_MESSAGE, PLANNER_MESSAGE, COMPANION_MESSAGE
from agent_messages import DYNAMIC_SELECTOR_MESSAGE, DYNAMIC_PLANNER_MESSAGE, DYNAMIC_COMPANION_MESSAGE

# Load environment variables
load_dotenv()

# Base LLM configuration
DEFAULT_LLM_CONFIG = {
    'cache_seed': 42,
    'temperature': 0.7,
    'top_p': 0.95,
    'config_list': [{
        'model': 'gpt-4o',
        'api_key': os.getenv('OPENAI_API_KEY'),
        'api_type': 'openai'
    }],
    'timeout': 1200
}

def create_selector_agent():
    """Create the restaurant selector agent with appropriate configurations."""
    selector_config = copy.deepcopy(DEFAULT_LLM_CONFIG)
    selector_config['config_list'][0]['response_format'] = RestaurantSelection
    
    agent = ConversableAgent(
        name="restaurant_selector",
        system_message=SELECTOR_MESSAGE,
        llm_config=selector_config,
        update_agent_state_before_reply=[UpdateSystemMessage(SELECTOR_MESSAGE)],
    )
    
    return agent

def create_planner_agent():
    """Create the route planner agent with appropriate configurations."""
    planner_config = copy.deepcopy(DEFAULT_LLM_CONFIG)
    planner_config['config_list'][0]['response_format'] = RoutePlan
    
    agent = ConversableAgent(
        name="route_planner",
        system_message=PLANNER_MESSAGE,
        llm_config=planner_config,
        update_agent_state_before_reply=[UpdateSystemMessage(PLANNER_MESSAGE)],
    )
    
    return agent

def create_companion_agent():
    """Create the companion agent with appropriate configurations."""
    companion_config = copy.deepcopy(DEFAULT_LLM_CONFIG)
    companion_config['config_list'][0]['response_format'] = CompanionOutput
    
    agent = ConversableAgent(
        name="companion",
        system_message=COMPANION_MESSAGE,
        llm_config=companion_config,
        update_agent_state_before_reply=[UpdateSystemMessage(COMPANION_MESSAGE)],
    )
    
    return agent

def setup_agent_handoffs(selector_agent, planner_agent, companion_agent):
    """Configure the handoff rules between agents."""
    # Set up handoffs between agents
    selector_agent.handoffs.set_after_work(AgentTarget(planner_agent))
    planner_agent.handoffs.set_after_work(AgentTarget(companion_agent))
    companion_agent.handoffs.set_after_work(TerminateTarget())
    
    # Add conditions for handoffs if needed
    from autogen.agentchat.group import StringLLMCondition, OnCondition
    
    selector_agent.handoffs.add_llm_conditions([
        OnCondition(
            target=AgentTarget(planner_agent),
            condition=StringLLMCondition(prompt="I have selected the restaurants and am ready to hand over to the route planner."),
        ),
    ])
    
    planner_agent.handoffs.add_llm_conditions([
        OnCondition(
            target=AgentTarget(companion_agent),
            condition=StringLLMCondition(prompt="I have planned the route and am ready to hand over to the companion agent."),
        ),
    ])
    
def create_agents():
    """Create and set up all agents with appropriate handoffs."""
    selector_agent = create_selector_agent()
    planner_agent = create_planner_agent()
    companion_agent = create_companion_agent()
    
    setup_agent_handoffs(selector_agent, planner_agent, companion_agent)
    
    return selector_agent, planner_agent, companion_agent 