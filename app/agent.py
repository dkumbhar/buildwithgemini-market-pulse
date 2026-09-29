# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import pathlib

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from .a2ui_utils import a2ui_callback
from .image_tools import generate_asset_image
from .maps_tools import find_nearby_places, geocode_address
from .portfolio_tools import (
    add_or_update_portfolio_item,
    calculate_portfolio_performance,
    fetch_exchange_rates,
    fetch_market_quote,
    get_asset_details,
    get_portfolio,
    simulate_investment_growth,
)
from .video_tools import generate_asset_video

# Read remote_agent_runtime_id from deployment_metadata.json if present
METADATA_FILE = pathlib.Path(__file__).parent.parent / "deployment_metadata.json"
AGENT_ENGINE_RESOURCE_NAME = "projects/971746460929/locations/us-east1/reasoningEngines/6757701818404306944"

if METADATA_FILE.exists():
    try:
        metadata = json.loads(METADATA_FILE.read_text())
        AGENT_ENGINE_RESOURCE_NAME = metadata.get("remote_agent_runtime_id", AGENT_ENGINE_RESOURCE_NAME)
    except Exception:
        pass


async def generate_memories_callback(callback_context: CallbackContext):
    """Sends session event history to Vertex AI Memory Bank for long-term memory extraction."""
    await callback_context.add_session_to_memory()
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are MarketPulse, an intelligent financial strategist and portfolio copilot. "
        "Help users analyze portfolio performance, check live currency/crypto exchange rates, "
        "look up real-time market quotes, manage positions in Firestore, simulate compound growth, "
        "geocode addresses, find nearby financial services, generate asset images and short videos, "
        "and recall user preferences or facts across sessions using long-term Memory Bank."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=AgentEngineSandboxCodeExecutor(
        agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME
    ),
    tools=[
        PreloadMemoryTool(),
        get_portfolio,
        get_asset_details,
        add_or_update_portfolio_item,
        calculate_portfolio_performance,
        fetch_market_quote,
        fetch_exchange_rates,
        simulate_investment_growth,
        geocode_address,
        find_nearby_places,
        generate_asset_image,
        generate_asset_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
