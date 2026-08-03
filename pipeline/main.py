"""collect -> validate -> store -> report 파이프라인 오케스트레이션."""

import asyncio
import logging
import sys

from pipeline.collectors import collect_all
from pipeline.schemas import CountryInfo, IPInfo, WeatherRecord, validate_batch, validate_single
from pipeline.storage import report, run_all_benchmarks

logger = logging.getLogger(__name__)


def _weather_items(raw_weather: dict) -> list[dict]:
    """Open-Meteo의 병렬 배열(hourly.time/temperature_2m/precipitation_probability)을
    WeatherRecord 검증용 딕셔너리 리스트로 변환한다."""
    hourly = raw_weather["hourly"]
    return [
        {"time": t, "temperature_2m": temp, "precipitation_probability": prob}
        for t, temp, prob in zip(
            hourly["time"],
            hourly["temperature_2m"],
            hourly["precipitation_probability"],
            strict=True,
        )
    ]


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    raw = await collect_all()

    # 소스별 수집 성공/실패를 명시적으로 로그로 남겨 "응답 정상 확인"을 눈으로 확인 가능하게 함
    for source in ("weather", "country", "ip"):
        payload = raw[source]
        if isinstance(payload, Exception):
            logger.error("%s: 수집 실패 - %s", source, payload)
        else:
            extra = f"({len(payload['hourly']['time'])} rows)" if source == "weather" else ""
            logger.info("%s: OK %s", source, extra)

    weather_valid: list[WeatherRecord] = []
    if not isinstance(raw["weather"], Exception):
        weather_valid, weather_errors = validate_batch(
            WeatherRecord, _weather_items(raw["weather"])
        )
        logger.info("weather 검증: 유효 %d건 / 무효 %d건", len(weather_valid), len(weather_errors))

    country_valid: CountryInfo | None = None
    if not isinstance(raw["country"], Exception):
        country_valid = validate_single(CountryInfo, raw["country"])
        logger.info("country 검증: %s", "유효" if country_valid else "무효")

    ip_valid: IPInfo | None = None
    if not isinstance(raw["ip"], Exception):
        ip_valid = validate_single(IPInfo, raw["ip"])
        logger.info("ip 검증: %s", "유효" if ip_valid else "무효")

    datasets = {
        "weather": weather_valid,
        "country": [country_valid] if country_valid else [],
        "ip": [ip_valid] if ip_valid else [],
    }

    if not any(datasets.values()):
        logger.error("모든 소스에서 유효 데이터가 없어 저장/성능 비교를 진행할 수 없습니다.")
        sys.exit(1)

    summary = run_all_benchmarks(datasets)
    report(summary)


if __name__ == "__main__":
    asyncio.run(main())
