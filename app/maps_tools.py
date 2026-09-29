# Copyright 2026 Google LLC
# Maps Geocoding and Places API (New) tools

import json
import os
import urllib.parse
import urllib.request
from typing import Any


def _get_api_key() -> str | None:
    return os.environ.get("GOOGLE_MAPS_API_KEY")


def geocode_address(address: str) -> dict[str, Any]:
    """Converts a street address or city name into geographic coordinates (latitude and longitude).

    Args:
        address: The address or location string to geocode (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        A dictionary containing formatted address, latitude, longitude, and status.
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MarketPulse/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"][0]
                loc = result["geometry"]["location"]
                return {
                    "formatted_address": result.get("formatted_address"),
                    "latitude": loc.get("lat"),
                    "longitude": loc.get("lng"),
                    "status": "OK",
                }
            return {"error": f"Geocoding failed: {data.get('status')}", "raw_response": data}
    except Exception as e:
        return {"error": f"Geocoding API error: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "bank",
    radius_meters: float = 1000.0,
) -> list[dict[str, Any]] | dict[str, Any]:
    """Finds nearby places of a specific type (e.g. bank, ATM, restaurant) near given coordinates using Places API (New).

    Args:
        latitude: Latitude coordinate.
        longitude: Longitude coordinate.
        place_type: Type of place to search for (e.g. 'bank', 'atm', 'accounting', 'establishment').
        radius_meters: Search radius in meters (default 1000m).

    Returns:
        A list of nearby places with name, address, and location coordinates.
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types",
    }

    body = {
        "includedTypes": [place_type.strip().lower()],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        data_bytes = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            places_raw = data.get("places", [])
            results = []
            for p in places_raw:
                loc = p.get("location", {})
                results.append({
                    "name": p.get("displayName", {}).get("text"),
                    "address": p.get("formattedAddress"),
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                    },
                    "types": p.get("types", []),
                })
            return results
    except Exception as e:
        return {"error": f"Places API (New) error: {str(e)}"}
