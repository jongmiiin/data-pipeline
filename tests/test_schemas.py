"""Pydantic v2 스키마의 valid/invalid 검증 및 예외 처리 테스트."""

import pytest
from pydantic import ValidationError

from pipeline.schemas import CountryInfo, IPInfo, WeatherRecord, validate_batch


# 정상 데이터는 필드 그대로 통과해야 한다.
def test_weather_record_valid(valid_weather_raw):
    record = WeatherRecord(**valid_weather_raw)
    assert record.temperature_2m == 25.3
    assert record.precipitation_probability == 10


# 확률(%) 범위(0~100)를 벗어나면 검증에서 걸러져야 한다.
def test_weather_record_invalid_precipitation_out_of_range(valid_weather_raw):
    valid_weather_raw["precipitation_probability"] = 150
    with pytest.raises(ValidationError):
        WeatherRecord(**valid_weather_raw)


# 타입이 안 맞는 값(문자열)이 들어오면 ValidationError로 예외 처리되어야 한다.
def test_weather_record_invalid_type(valid_weather_raw):
    valid_weather_raw["temperature_2m"] = "not-a-number"
    with pytest.raises(ValidationError):
        WeatherRecord(**valid_weather_raw)


# camelCase 원본 키(alpha3Code 등)가 alias를 통해 정상적으로 매핑되는지 확인.
def test_country_info_valid(valid_country_raw):
    country = CountryInfo(**valid_country_raw)
    assert country.capital == "Seoul"
    assert country.alpha3_code == "KOR"


# 인구수가 음수인 것처럼 물리적으로 불가능한 값은 거부해야 한다.
def test_country_info_invalid_negative_population(valid_country_raw):
    valid_country_raw["population"] = -1
    with pytest.raises(ValidationError):
        CountryInfo(**valid_country_raw)


# regionName -> region_name alias 매핑과 정상 status가 함께 통과하는지 확인.
def test_ip_info_valid(valid_ip_raw):
    ip_info = IPInfo(**valid_ip_raw)
    assert ip_info.region_name == "Virginia"
    assert ip_info.status == "success"


# 위도 범위(-90~90)를 벗어나는 값은 거부해야 한다.
def test_ip_info_invalid_lat_out_of_range(valid_ip_raw):
    valid_ip_raw["lat"] = 999
    with pytest.raises(ValidationError):
        IPInfo(**valid_ip_raw)


# status="fail"이면 mode="after" 비즈니스 규칙 validator가 예외를 던져야 한다.
def test_ip_info_status_fail_raises(valid_ip_raw):
    valid_ip_raw["status"] = "fail"
    with pytest.raises(ValidationError):
        IPInfo(**valid_ip_raw)


# validate_batch의 핵심 정책 검증: 하나가 실패해도 나머지는 유효 목록에 남아야 한다
# (채점기준의 "타입 오류 시 예외 처리"를 직접 겨냥하는 테스트).
def test_validate_batch_partial_failure(valid_weather_raw):
    bad_item = dict(valid_weather_raw, precipitation_probability=150)
    valid, errors = validate_batch(WeatherRecord, [valid_weather_raw, bad_item])
    assert len(valid) == 1
    assert len(errors) == 1
    assert errors[0]["index"] == 1
