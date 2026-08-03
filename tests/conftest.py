"""테스트에서 공통으로 쓰는 샘플 raw JSON fixture (실제 API 응답 형태를 모사)."""

import pytest


@pytest.fixture
def valid_weather_raw() -> dict:
    return {
        "time": "2026-08-03T00:00",
        "temperature_2m": 25.3,
        "precipitation_probability": 10,
    }


@pytest.fixture
def valid_country_raw() -> dict:
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
    return {
        "status": "success",
        "query": "8.8.8.8",
        "country": "United States",
        "regionName": "Virginia",
        "city": "Ashburn",
        "lat": 39.03,
        "lon": -77.5,
    }
