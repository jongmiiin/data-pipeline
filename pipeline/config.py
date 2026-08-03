"""API 엔드포인트, 타임아웃, 출력 경로 등 파이프라인 전역 상수."""

from pathlib import Path

# 서울(위도 37.5665, 경도 126.9780) 3일치 시간대별 기온·강수확률
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=37.5665&longitude=126.9780"
    "&hourly=temperature_2m,precipitation_probability"
    "&forecast_days=3&timezone=Asia/Seoul"
)

COUNTRY_URL = "https://countries.dev/alpha/KOR"

# ip-api.com 무료 티어는 HTTPS를 지원하지 않는다(유료 플랜 전용).
# http -> https로 자동 업그레이드하면 403이 반환되므로 반드시 http:// 리터럴로 호출해야 한다.
IP_URL = "http://ip-api.com/json/8.8.8.8"

HTTP_TIMEOUT_SECONDS = 10.0

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_DIR = DATA_DIR / "csv"
PARQUET_DIR = DATA_DIR / "parquet"
PERF_SUMMARY_PATH = DATA_DIR / "performance_summary.json"
