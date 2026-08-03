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

    # 1) 수집: 3개 API를 동시에 호출한다. 실패한 소스는 예외 객체로 담겨오므로
    #    아래에서 isinstance(payload, Exception)으로 구분해서 처리한다.
    raw = await collect_all()

    # 소스별 수집 성공/실패를 명시적으로 로그로 남겨 "응답 정상 확인"을 눈으로 확인 가능하게 함
    for source in ("weather", "country", "ip"):
        payload = raw[source]
        if isinstance(payload, Exception):
            logger.error("%s: 수집 실패 - %s", source, payload)
        else:
            # weather는 72개 시간대별 레코드라 행 수를 같이 찍어준다.
            extra = f"({len(payload['hourly']['time'])} rows)" if source == "weather" else ""
            logger.info("%s: OK %s", source, extra)

    # 2) 검증: 수집이 성공한 소스만 Pydantic 모델로 타입·범위 검증한다.
    #    수집 자체가 실패한 소스(Exception)는 애초에 검증할 데이터가 없으므로 건너뛴다.
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

    # country/ip는 1건짜리라 유효하면 리스트에 담고, 무효면 빈 리스트로 두어
    # weather와 동일한 "list[BaseModel]" 형태로 storage 계층에 넘긴다.
    datasets = {
        "weather": weather_valid,
        "country": [country_valid] if country_valid else [],
        "ip": [ip_valid] if ip_valid else [],
    }

    if not any(datasets.values()):
        logger.error("모든 소스에서 유효 데이터가 없어 저장/성능 비교를 진행할 수 없습니다.")
        sys.exit(1)

    # 3) 저장 및 성능 비교: 유효한 데이터셋만 CSV/Parquet로 저장하고 결과를 출력한다.
    summary = run_all_benchmarks(datasets)
    report(summary)


if __name__ == "__main__":
    asyncio.run(main())
