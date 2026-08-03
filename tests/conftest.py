"""테스트에서 공통으로 쓰는 샘플 raw JSON fixture (실제 API 응답 형태를 모사)."""

import pytest


@pytest.fixture
def valid_weather_raw() -> dict:
    """Open-Meteo hourly 배열에서 한 시간대만 꺼낸 형태."""
    return {
        "time": "2026-08-03T00:00",
        "temperature_2m": 25.3,
        "precipitation_probability": 10,
    }


@pytest.fixture
def valid_country_raw() -> dict:
    """countries.dev/alpha/KOR 실제 응답 형태(camelCase 필드 포함)를 그대로 모사."""
    return {
        "name": "Korea (Republic of)",
        "capital": "Seoul",
        "region": "Asia",
        "population": 51780579,
        "area": 100210,
        "alpha2Code": "KR",
        "alpha3Code": "KOR",
        "nativeName": "대한민국",
    }


@pytest.fixture
def valid_ip_raw() -> dict:
    """ip-api.com/json/8.8.8.8 실제 응답에서 우리가 쓰는 필드만 추린 형태."""
    return {
        "status": "success",
        "query": "8.8.8.8",
        "country": "United States",
        "regionName": "Virginia",
        "city": "Ashburn",
        "lat": 39.03,
        "lon": -77.5,
    }
