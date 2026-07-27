"""weather 서버 테스트 — 네트워크 없이 _get_json을 patch해 in-memory MCP 세션으로 검증.

이 파일이 서버 테스트의 본보기다: 다른 서버 테스트도 같은 구조를 따른다.
"""

import json

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

import jarvis_mcp.weather.server as weather

GEOCODE_RESPONSE = {
    "results": [
        {"name": "서울", "latitude": 37.57, "longitude": 126.98, "timezone": "Asia/Seoul", "country": "대한민국"}
    ]
}


@pytest.fixture(autouse=True)
def fake_http(monkeypatch):
    async def _fake_get_json(url, params):
        if "geocoding" in url:
            return GEOCODE_RESPONSE
        if "current" in params:
            return {"current": {"temperature_2m": 29.1}, "current_units": {"temperature_2m": "°C"}}
        if "hourly" in params:
            return {"hourly": {"temperature_2m": [29, 30]}, "hourly_units": {}}
        return {"daily": {"temperature_2m_max": [31]}, "daily_units": {}}

    monkeypatch.setattr(weather, "_get_json", _fake_get_json)


def _payload(result):
    assert not result.isError, result.content
    return json.loads(result.content[0].text)


async def test_tools_are_listed():
    async with create_connected_server_and_client_session(weather.mcp) as session:
        tools = {tool.name for tool in (await session.list_tools()).tools}
    assert tools == {"get_current_weather", "get_hourly_forecast", "get_daily_forecast", "get_weather_alerts"}


async def test_current_weather_returns_location_and_data():
    async with create_connected_server_and_client_session(weather.mcp) as session:
        payload = _payload(await session.call_tool("get_current_weather", {"location": "서울"}))
    assert payload["location"]["name"] == "서울"
    assert payload["current"]["temperature_2m"] == 29.1


async def test_unknown_location_is_a_tool_error(monkeypatch):
    async def _empty(url, params):
        return {"results": []}

    monkeypatch.setattr(weather, "_get_json", _empty)
    async with create_connected_server_and_client_session(weather.mcp) as session:
        result = await session.call_tool("get_current_weather", {"location": "없는곳"})
    assert result.isError


async def test_alerts_always_returns_list():
    async with create_connected_server_and_client_session(weather.mcp) as session:
        payload = _payload(await session.call_tool("get_weather_alerts", {"location": "서울"}))
    assert payload["alerts"] == []
