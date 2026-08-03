"""3개 API 응답에 대한 Pydantic v2 검증 모델과 공통 검증 헬퍼."""

import logging
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

logger = logging.getLogger(__name__)


class WeatherRecord(BaseModel):
    """Open-Meteo 서울 시간대별 예보 한 건."""

    time: datetime
    temperature_2m: float
    # 확률(%) 값이라 0~100 범위를 벗어나면 API가 이상한 값을 준 것으로 보고 걸러낸다.
    precipitation_probability: int = Field(ge=0, le=100)


class CountryInfo(BaseModel):
    """Countries.dev(alpha/KOR) 응답 중 필요한 필드만 검증한 국가 정보.

    이 API는 REST Countries v2 스타일의 평평한(flat) JSON을 반환하므로
    (예: `name`, `capital`이 모두 단일 문자열) 별도 평탄화 로직 없이
    Field alias만으로 camelCase 원본 키를 그대로 매핑한다.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str
    capital: str
    region: str
    population: int = Field(ge=0)  # 인구/면적이 음수면 명백히 잘못된 데이터
    area: float = Field(ge=0)
    # ISO 3166-1 alpha-2/alpha-3 코드는 길이가 고정이라 min/max_length로 형식까지 검증
    alpha2_code: str = Field(alias="alpha2Code", min_length=2, max_length=2)
    alpha3_code: str = Field(alias="alpha3Code", min_length=3, max_length=3)
    native_name: str | None = Field(default=None, alias="nativeName")


class IPInfo(BaseModel):
    """ip-api.com(8.8.8.8) 조회 결과 중 필요한 필드만 검증한 위치 정보."""

    model_config = ConfigDict(populate_by_name=True)

    status: Literal["success", "fail"]
    query: str
    country: str
    region_name: str = Field(alias="regionName")
    city: str
    lat: float = Field(ge=-90, le=90)  # 위도/경도의 물리적으로 가능한 범위
    lon: float = Field(ge=-180, le=180)

    @model_validator(mode="after")
    def _check_status_success(self) -> "IPInfo":
        """ip-api가 status="fail"을 반환하면(예: 조회 실패) 검증 오류로 취급한다."""
        if self.status != "success":
            raise ValueError("ip-api 조회 status가 'success'가 아님")
        return self


def validate_batch(
    model_cls: type[BaseModel], raw_items: list[dict]
) -> tuple[list[BaseModel], list[dict]]:
    """레코드 단위로 검증한다.

    한 레코드가 실패해도 나머지는 계속 검증하도록 전체를 한 번에 모델링하지 않고
    항목별로 개별 try/except를 수행한다. 실패한 레코드는 인덱스와 에러 상세를
    errors 리스트에 담아 반환하며, 호출부는 이를 로깅하고 계속 진행할 수 있다.
    """
    valid: list[BaseModel] = []
    errors: list[dict] = []
    for i, item in enumerate(raw_items):
        try:
            valid.append(model_cls(**item))
        except ValidationError as exc:
            # 실패한 레코드는 건너뛰고 계속 진행한다 — 여기서 raise하면
            # weather의 나머지 71개 정상 레코드까지 전부 버려지게 된다.
            errors.append({"index": i, "errors": exc.errors()})
            logger.warning("%s[%d] 검증 실패: %s", model_cls.__name__, i, exc.errors())
    return valid, errors


def validate_single(model_cls: type[BaseModel], raw_item: dict) -> BaseModel | None:
    """단일 레코드(country/ip처럼 1건짜리 응답)를 검증한다. 실패 시 None과 로그."""
    valid, _ = validate_batch(model_cls, [raw_item])
    return valid[0] if valid else None
