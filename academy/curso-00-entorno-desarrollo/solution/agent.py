"""
Solution: Your first AI agent with multiple tools

This agent can:
1. Get weather for a city
2. Calculate mathematical expressions
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.tools import Tool

load_dotenv()

# Define tools that the agent can use
def get_weather(location: str) -> str:
    """Gets the current weather for a location."""
    weather_data = {
        "buenos aires": "22°C, clear skies ☀️",
        "new york": "15°C, cloudy 🌥️",
        "london": "12°C, rainy 🌧️",
        "tokyo": "28°C, sunny ☀️",
        "sydney": "25°C, partly cloudy ⛅"
    }
    loc = location.lower()
    return weather_data.get(loc, f"Weather for {location} not found in database")

def calculator(expression: str) -> str:
    """Executes a mathematical expression safely."""
    try:
        # Safe evaluation of basic math
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error calculating: {e}"

# Wrap tools for LangChain
tools = [
    Tool(
        name="WeatherTool",
        func=get_weather,
        description="Gets the current weather for a city. Input: city name (e.g., 'Buenos Aires')"
    ),
    Tool(
        name="Calculator",
        func=calculator,
        description="Calculates a mathematical expression. Input: expression (e.g., '2+2*3' or '15% of 200')"
    )
]

# Create LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Create agent
agent_prompt = hub.pull("hwchase17/openai-functions-agent")
agent = create_openai_functions_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    # Example 1: Ask about weather in multiple cities
    print("\n" + "="*60)
    print("EXAMPLE 1: Compare weather in two cities")
    print("="*60)
    result = agent_executor.invoke({
        "input": "What's the weather in Buenos Aires and New York? Which is warmer?"
    })
    print(f"\nAgent's Answer:\n{result['output']}\n")

    # Example 2: Ask agent to do math and compare
    print("\n" + "="*60)
    print("EXAMPLE 2: Do math")
    print("="*60)
    result = agent_executor.invoke({
        "input": "Calculate 20% of $500 and 15% of $600. Which is bigger?"
    })
    print(f"\nAgent's Answer:\n{result['output']}\n")

    # Example 3: Combined task
    print("\n" + "="*60)
    print("EXAMPLE 3: Combine weather and math")
    print("="*60)
    result = agent_executor.invoke({
        "input": "The temperature in Tokyo is 28°C. Convert that to Fahrenheit (formula: C * 9/5 + 32). Also tell me if that's warmer than London."
    })
    print(f"\nAgent's Answer:\n{result['output']}\n")
