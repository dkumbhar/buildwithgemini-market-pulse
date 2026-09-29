# Copyright 2026 Google LLC
# Image generation tool for MarketPulse financial assets

import time
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

GCS_BUCKET_NAME = "market-pulse-assets-qwiklabs-gcp-01-f582106045c5"


def generate_asset_image(prompt: str, tool_context: ToolContext) -> dict[str, str]:
    """Generates a visual image for a financial asset, investment milestone, or market concept.

    Generates the image using gemini-3.1-flash-lite-image in the global region,
    saves it as a tool artifact in Playground, and uploads the image bytes directly to Cloud Storage.

    Args:
        prompt: Detailed visual description of the financial image to generate.

    Returns:
        A dictionary containing the filename, public Cloud Storage HTTPS URL, and confirmation status.
    """
    client = genai.Client(location="global")

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    image_bytes = None
    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                break

    if not image_bytes:
        return {"error": "Failed to generate image bytes from model response."}

    filename = f"asset_image_{int(time.time())}.png"

    # 1. Save artifact in Playground
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes directly to GCS bucket
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type="image/png")

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

    return {
        "filename": filename,
        "public_url": public_url,
        "status": "Image generated, saved as artifact, and uploaded to Cloud Storage successfully.",
    }
