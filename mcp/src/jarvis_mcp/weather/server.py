"""Weather MCP 서버 (Part 12 §6) — Open-Meteo 기반, API 키 불필요.

도구: get_current_weather / get_hourly_forecast / get_daily_forecast / get_weather_alerts
"""

from __future__ import annotations

from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

#: Open-Meteo 지오코딩은 한국어 지명을 일관되게 못 찾는다 ("서울"은 0건, "부산"은 성공).
#: 실패 시 모델이 영어로 재질의하느라 LLM 라운드가 통째로 낭비되므로 여기서 바로 보정한다.
_KO_CITY_ALIASES = {
    "서울": "Seoul", "서울시": "Seoul", "서울특별시": "Seoul",
    "부산": "Busan", "인천": "Incheon", "대구": "Daegu", "대전": "Daejeon",
    "광주": "Gwangju", "울산": "Ulsan", "세종": "Sejong", "수원": "Suwon",
    "성남": "Seongnam", "고양": "Goyang", "용인": "Yongin", "창원": "Changwon",
    "청주": "Cheongju", "전주": "Jeonju", "천안": "Cheonan", "제주": "Jeju",
    "춘천": "Chuncheon", "강릉": "Gangneung", "포항": "Pohang", "여수": "Yeosu",
}
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

mcp = FastMCP("weather")


async def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    """외부 호출 지점 — 테스트에서 monkeypatch 한다."""
    async with httpx.AsyncClient(timeout=8.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def _lookup(name: str) -> list[dict[str, Any]]:
    data = await _get_json(GEOCODE_URL, {"name": name, "count": 1, "language": "ko"})
    return data.get("results") or []


#: 도시 좌표는 변하지 않는다 — 매 질의마다 왕복할 이유가 없다.
#: 음성 응답에서는 이 왕복 하나가 그대로 체감 지연이 된다.
_GEOCODE_CACHE: dict[str, dict[str, Any]] = {}


async def _geocode(location: str) -> dict[str, Any]:
    key = location.strip()
    if cached := _GEOCODE_CACHE.get(key):
        return cached

    results = await _lookup(location)

    if not results:
        # 한국어 지명이 안 잡히면 영문 표기로 한 번 더 시도한다.
        alias = _KO_CITY_ALIASES.get(location.strip())
        if alias:
            results = await _lookup(alias)

    if not results:
        raise ToolError(f"위치를 찾을 수 없습니다: {location}")
    top = results[0]
    place = {
        "name": top["name"],
        "latitude": top["latitude"],
        "longitude": top["longitude"],
        "timezone": top.get("timezone", "Asia/Seoul"),
        "country": top.get("country"),
    }
    _GEOCODE_CACHE[key] = place
    return place


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
