# data-pipeline

Day1 종합 실습 — 실무형 수집·검증·품질 파이프라인. Open-Meteo(서울 3일 기온·강수확률), Countries.dev(한국 국가 정보), ip-api(IP 지역 정보) 3개 공개 API를 비동기로 수집하고, Pydantic v2로 검증한 뒤 CSV/Parquet로 저장하며 성능을 비교한다.

## 환경 설정

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 실행

```bash
python -m pipeline.main
```

3개 API를 동시에 수집하고, 검증 결과와 CSV/Parquet 저장 성능 비교 결과를 콘솔에 출력한다. 성능 비교 결과는 `data/performance_summary.json`에도 저장된다.

## 테스트 / 린트

```bash
pytest -v
ruff check .
```
