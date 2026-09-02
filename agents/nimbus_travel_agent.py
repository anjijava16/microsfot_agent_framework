import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
from agent_framework import Agent, tool
from agent_framework.openai import OpenAIChatClient
from monocle_apptrace import setup_monocle_telemetry

# Enable Monocle Tracing
setup_monocle_telemetry(
    workflow_name="okahu_demos_ms_openai_travel_agent",
    monocle_exporters_list="file",
)


# Tool implementations
@tool(approval_mode="never_require")
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for flights between two cities on a given date."""
    # stub - replace with real API call
    return (
        f"Found 3 flights from {origin} to {destination} on {date}: "
        f"Delta $320, United $290, JetBlue $275"
    )


@tool(approval_mode="never_require")
def search_hotels(city: str, checkin: str, checkout: str) -> str:
    """Search for hotels in a city for given dates."""
    return (
        f"Found hotels in {city} ({checkin} to {checkout}): "
        f"Marriott $180/night, Hilton $165/night, Airbnb $120/night"
    )
NEBIUS_API_KEY='v1.CmMKHHN0YXRpY2tleS1lMDBjdGRmMWgyMzRwOTFoeXASIXNlcnZpY2VhY2NvdW50LWUwMHZxdG1zNWFhd2gwMGU1dDILCIyT1dEGELqKhhQ6DAiLlu2cBxDAhqLnAUACWgNlMDA.AAAAAAAAAAEkrfZ-eprJPHslLLiR796cllCOzcIn2iPL-i8XAz5zDcDw-wEfDM8IjDDuqIwIJknnrmxTNM2v4agxZoZ5xMUM'
from openai import OpenAI
client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=NEBIUS_API_KEY
)

# from agent_framework.openai import OpenAIChatClient

# client = OpenAIChatClient(
#     api_key=NEBIUS_API_KEY,
#     base_url="https://api.tokenfactory.nebius.com/v1/",
#     model="Qwen/Qwen3.5-397B-A17B"
# )

from agent_framework.openai import OpenAIChatCompletionClient
client = OpenAIChatCompletionClient(
    model="Qwen/Qwen3.5-397B-A17B",
    api_key=NEBIUS_API_KEY,
    base_url="https://api.tokenfactory.nebius.com/v1/",
)
# Agent instantiation
agent = Agent(
    client=client,
    #OpenAIChatClient(base_url="https://api.tokenfactory.nebius.com/v1", api_key=NEBIUS_API_KEY ),
    name="TravelAgent",
    instructions=(
        "You are a helpful travel planning assistant. "
        "Use the available tools to find flights and hotels, "
        "then summarize the best options with a short itinerary."
    ),
    tools=[search_flights, search_hotels],
)


async def main():
    result = await agent.run(
        "Plan a trip from New York to San Francisco, "
        "departing 2026-07-10 and returning 2026-07-14."
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
