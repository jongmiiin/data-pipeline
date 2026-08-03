"""Pydantic v2 스키마의 valid/invalid 검증 및 예외 처리 테스트."""

import pytest
from pydantic import ValidationError

from pipeline.schemas import CountryInfo, IPInfo, WeatherRecord, validate_batch


def test_weather_record_valid(valid_weather_raw):
    record = WeatherRecord(**valid_weather_raw)
    assert record.temperature_2m == 25.3
    assert record.precipitation_probability == 10


def test_weather_record_invalid_precipitation_out_of_range(valid_weather_raw):
    valid_weather_raw["precipitation_probability"] = 150
    with pytest.raises(ValidationError):
        WeatherRecord(**valid_weather_raw)


def test_weather_record_invalid_type(valid_weather_raw):
    valid_weather_raw["temperature_2m"] = "not-a-number"
    with pytest.raises(ValidationError):
        WeatherRecord(**valid_weather_raw)


def test_country_info_valid(valid_country_raw):
    country = CountryInfo(**valid_country_raw)
    assert country.capital == "Seoul"
    assert country.alpha3_code == "KOR"


def test_country_info_invalid_negative_population(valid_country_raw):
    valid_country_raw["population"] = -1
    with pytest.raises(ValidationError):
        CountryInfo(**valid_country_raw)


def test_ip_info_valid(valid_ip_raw):
    ip_info = IPInfo(**valid_ip_raw)
    assert ip_info.region_name == "Virginia"
    assert ip_info.status == "success"


def test_ip_info_invalid_lat_out_of_range(valid_ip_raw):
    valid_ip_raw["lat"] = 999
    with pytest.raises(ValidationError):
        IPInfo(**valid_ip_raw)


def test_ip_info_status_fail_raises(valid_ip_raw):
    valid_ip_raw["status"] = "fail"
    with pytest.raises(ValidationError):
        IPInfo(**valid_ip_raw)


def test_validate_batch_partial_failure(valid_weather_raw):
    bad_item = dict(valid_weather_raw, precipitation_probability=150)
    valid, errors = validate_batch(WeatherRecord, [valid_weather_raw, bad_item])
    assert len(valid) == 1
    assert len(errors) == 1
    assert errors[0]["index"] == 1
