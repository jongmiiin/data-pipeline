"""CSV/Parquet 저장 및 읽기·쓰기 성능 측정·비교."""

import json
import time
from typing import Any

import pandas as pd
from pydantic import BaseModel

from pipeline.config import CSV_DIR, PARQUET_DIR, PERF_SUMMARY_PATH


def _timed(fn, *args, **kwargs) -> tuple[Any, float]:
    """fn(*args, **kwargs)을 실행하고 (결과, 경과시간(초))를 반환한다."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    return result, time.perf_counter() - start


def benchmark_dataset(name: str, records: list[BaseModel]) -> dict:
    """레코드 목록 하나를 CSV/Parquet로 저장·재로드하며 시간과 용량을 측정한다.

    country/ip처럼 1행짜리 데이터셋은 단일 실행 측정이라 노이즈가 있을 수 있지만,
    이 실습 범위에서는 반복 측정(N회 평균)까지는 하지 않는다.
    """
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)

    # Pydantic 모델 리스트 -> dict 리스트 -> DataFrame 순으로 변환
    df = pd.DataFrame([r.model_dump() for r in records])
    csv_path = CSV_DIR / f"{name}.csv"
    parquet_path = PARQUET_DIR / f"{name}.parquet"

    # 쓰기 먼저, 그다음 방금 쓴 파일을 다시 읽어서 읽기 시간까지 함께 측정한다.
    _, csv_write_s = _timed(df.to_csv, csv_path, index=False)
    _, csv_read_s = _timed(pd.read_csv, csv_path)
    _, parquet_write_s = _timed(df.to_parquet, parquet_path, index=False)
    _, parquet_read_s = _timed(pd.read_parquet, parquet_path)

    return {
        "dataset": name,
        "rows": len(df),
        "csv_write_s": csv_write_s,
        "csv_read_s": csv_read_s,
        "parquet_write_s": parquet_write_s,
        "parquet_read_s": parquet_read_s,
        "csv_bytes": csv_path.stat().st_size,
        "parquet_bytes": parquet_path.stat().st_size,
    }


def run_all_benchmarks(datasets: dict[str, list[BaseModel]]) -> pd.DataFrame:
    """데이터셋별 벤치마크 결과를 하나의 요약 DataFrame으로 모은다."""
    # records가 빈 리스트인 데이터셋(검증 전부 실패 등)은 저장할 게 없으니 건너뛴다.
    rows = [benchmark_dataset(name, records) for name, records in datasets.items() if records]
    return pd.DataFrame(rows)


def _comparison_sentence(row: pd.Series) -> str:
    """행 하나를 읽고 CSV 대비 Parquet의 읽기/쓰기 속도 차이를 배수(倍数)로 요약한다.

    행 수가 적은 데이터셋은 Parquet의 스키마/메타데이터 기록 오버헤드가 상대적으로
    커서 CSV보다 몇 배 느리게 나올 수 있다 — 퍼센트로 표시하면 수천 %까지 치솟아
    가독성이 떨어지므로 배수로 표현한다.
    """

    def ratio_phrase(csv_s: float, parquet_s: float) -> str:
        if csv_s == 0 or parquet_s == 0:
            return "비교 불가(0초)"
        if parquet_s < csv_s:
            return f"{csv_s / parquet_s:.1f}배 빠름"
        return f"{parquet_s / csv_s:.1f}배 느림"

    write_cmp = ratio_phrase(row["csv_write_s"], row["parquet_write_s"])
    read_cmp = ratio_phrase(row["csv_read_s"], row["parquet_read_s"])
    return f"[{row['dataset']}] Parquet vs CSV — 쓰기: {write_cmp}, 읽기: {read_cmp}"


def report(summary_df: pd.DataFrame) -> None:
    """성능 비교 결과를 콘솔 표 + 비교 문장으로 출력하고 JSON으로도 저장한다."""
    # 3개 소스 모두 검증에 실패해 datasets가 전부 비어 있으면 여기로 온다.
    if summary_df.empty:
        print("저장할 유효 데이터셋이 없어 성능 비교를 생략합니다.")
        return

    print("\n=== 저장 성능 비교 (초 / 바이트) ===")
    print(summary_df.to_string(index=False))

    print("\n=== 비교 요약 ===")
    for _, row in summary_df.iterrows():
        print(_comparison_sentence(row))

    PERF_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    PERF_SUMMARY_PATH.write_text(
        json.dumps(summary_df.to_dict(orient="records"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n성능 비교 결과를 {PERF_SUMMARY_PATH}에 저장했습니다.")
