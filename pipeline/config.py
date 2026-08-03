"""API 엔드포인트, 타임아웃, 출력 경로 등 파이프라인 전역 상수."""

from pathlib import Path

# 서울(위도 37.5665, 경도 126.9780) 3일치 시간대별 기온·강수확률
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=37.5665&longitude=126.9780"
    "&hourly=temperature_2m,precipitation_probability"
    "&forecast_days=3&timezone=Asia/Seoul"
)

# alpha3 코드(KOR)로 한국 국가 정보 조회. 다른 나라를 보고 싶으면 이 부분만 바꾸면 된다.
COUNTRY_URL = "https://countries.dev/alpha/KOR"

# ip-api.com 무료 티어는 HTTPS를 지원하지 않는다(유료 플랜 전용).
# http -> https로 자동 업그레이드하면 403이 반환되므로 반드시 http:// 리터럴로 호출해야 한다.
IP_URL = "http://ip-api.com/json/8.8.8.8"

# 3개 API 모두 공용으로 쓰는 요청 타임아웃(초 단위). 하나라도 이 시간을 넘기면
# httpx.TimeoutException이 발생해 collectors.py에서 CollectionError로 처리된다.
HTTP_TIMEOUT_SECONDS = 10.0

# 이 파일(config.py) 기준으로 프로젝트 루트(data-pipeline/)를 계산해,
# 실행 위치(cwd)와 상관없이 항상 같은 data/ 경로를 가리키도록 한다.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_DIR = DATA_DIR / "csv"
PARQUET_DIR = DATA_DIR / "parquet"
PERF_SUMMARY_PATH = DATA_DIR / "performance_summary.json"
