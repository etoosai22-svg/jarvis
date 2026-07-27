"""Weather MCP 서버 (Part 12 §6) — Open-Meteo 기반, API 키 불필요.

도구: get_current_weather / get_hourly_forecast / get_daily_forecast / get_weather_alerts
"""

from __future__ import annotations

from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

mcp = FastMCP("weather")


async def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    """외부 호출 지점 — 테스트에서 monkeypatch 한다."""
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def _geocode(location: str) -> dict[str, Any]:
    data = await _get_json(GEOCODE_URL, {"name": location, "count": 1, "language": "ko"})
    results = data.get("results") or []
    if not results:
        raise ToolError(f"위치를 찾을 수 없습니다: {location}")
    top = results[0]
    return {
        "name": top["name"],
        "latitude": top["latitude"],
        "longitude": top["longitude"],
        "timezone": top.get("timezone", "Asia/Seoul"),
        "country": top.get("country"),
    }


@mcp.tool()
async def get_current_weather(location: str) -> dict[str, Any]:
    """현재 날씨를 조회한다. location은 도시명 (예: '서울')."""
    place = await _geocode(location)
    data = await _get_json(
        FORECAST_URL,
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,weather_code,wind_speed_10m",
            "timezone": place["timezone"],
        },
    )
    return {"location": place, "current": data.get("current", {}), "units": data.get("current_units", {}), "source": "open-meteo"}


@mcp.tool()
async def get_hourly_forecast(location: str, hours: int = 12) -> dict[str, Any]:
    """시간별 예보를 조회한다 (기본 12시간, 최대 48시간)."""
    hours = max(1, min(hours, 48))
    place = await _geocode(location)
    data = await _get_json(
        FORECAST_URL,
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "hourly": "temperature_2m,precipitation_probability,precipitation,weather_code",
            "forecast_hours": hours,
            "timezone": place["timezone"],
        },
    )
    return {"location": place, "hourly": data.get("hourly", {}), "units": data.get("hourly_units", {}), "source": "open-meteo"}


@mcp.tool()
async def get_daily_forecast(location: str, days: int = 7) -> dict[str, Any]:
    """일별 예보를 조회한다 (기본 7일, 최대 16일)."""
    days = max(1, min(days, 16))
    place = await _geocode(location)
    data = await _get_json(
        FORECAST_URL,
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            "forecast_days": days,
            "timezone": place["timezone"],
        },
    )
    return {"location": place, "daily": data.get("daily", {}), "units": data.get("daily_units", {}), "source": "open-meteo"}


@mcp.tool()
async def get_weather_alerts(location: str) -> dict[str, Any]:
    """기상 특보를 조회한다. Open-Meteo는 특보를 제공하지 않아 항상 빈 목록이다."""
    place = await _geocode(location)
    return {
        "location": place,
        "alerts": [],
        "note": "Open-Meteo는 기상 특보를 제공하지 않습니다. 특보 제공자 연동 전까지 빈 목록을 반환합니다.",
        "source": "open-meteo",
    }
