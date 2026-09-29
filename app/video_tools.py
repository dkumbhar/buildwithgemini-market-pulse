# Copyright 2026 Google LLC
# Video generation tool for MarketPulse financial assets using gemini-omni-flash-preview

import base64
import time
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

GCS_BUCKET_NAME = "market-pulse-assets-qwiklabs-gcp-01-f582106045c5"


def generate_asset_video(prompt: str, tool_context: ToolContext) -> dict[str, str]:
    """Generates a short animated video for a financial asset, market trend, or investment goal.

    Generates the video using gemini-omni-flash-preview in the global region,
    saves it as a tool artifact in Playground, and uploads the video bytes directly to Cloud Storage.

    Args:
        prompt: Visual description of the short financial video to generate.

    Returns:
        A dictionary containing the filename, public Cloud Storage HTTPS URL, and status.
    """
    client = genai.Client(vertexai=True, location="global")

    interaction = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt,
    )

    output_video = getattr(interaction, "output_video", None)
    raw_data = getattr(output_video, "data", None) if output_video else None

    if not raw_data:
        return {"error": "Failed to generate video data from gemini-omni-flash-preview model."}

    if isinstance(raw_data, str):
        video_bytes = base64.b64decode(raw_data)
    else:
        video_bytes = bytes(raw_data)

    filename = f"asset_video_{int(time.time())}.mp4"

    # 1. Save artifact in Playground
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload video bytes directly to public GCS bucket
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type="video/mp4")

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

    return {
        "filename": filename,
        "public_url": public_url,
        "status": "Video generated, saved as artifact, and uploaded to Cloud Storage successfully.",
    }
