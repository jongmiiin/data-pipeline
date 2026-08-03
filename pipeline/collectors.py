"""httpx + asyncio.gather를 사용한 3개 API 동시 수집."""

import asyncio

import httpx

from pipeline.config import COUNTRY_URL, HTTP_TIMEOUT_SECONDS, IP_URL, WEATHER_URL


class CollectionError(Exception):
    """API 수집 실패를 소스 이름과 함께 감싸는 예외."""

    def __init__(self, source: str, original: Exception) -> None:
        self.source = source
        self.original = original
        super().__init__(f"{source} 수집 실패: {original!r}")


async def _fetch_json(client: httpx.AsyncClient, source: str, url: str) -> dict:
    """URL을 GET하고 상태코드를 확인한 뒤 JSON을 반환한다. 실패 시 CollectionError로 래핑."""
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        raise CollectionError(source, exc) from exc


async def fetch_weather(client: httpx.AsyncClient) -> dict:
    """서울 3일 시간대별 기온·강수확률(Open-Meteo)을 가져온다."""
    return await _fetch_json(client, "weather", WEATHER_URL)


async def fetch_country(client: httpx.AsyncClient) -> dict:
    """한국 국가 정보(Countries.dev)를 가져온다."""
    return await _fetch_json(client, "country", COUNTRY_URL)


async def fetch_ip_info(client: httpx.AsyncClient) -> dict:
    """IP 기반 지역 정보(ip-api)를 가져온다.

    ip-api.com 무료 티어는 HTTP만 지원하므로 config.IP_URL의 http:// 스킴을
    그대로 사용해야 한다(https로 호출하면 403).
    """
    return await _fetch_json(client, "ip", IP_URL)


async def collect_all() -> dict[str, dict | Exception]:
    """3개 API를 asyncio.gather()로 동시에 수집한다.

    return_exceptions=True로 실행해, 한 API가 실패해도 다른 두 개의 진행 중인
    요청이 취소되지 않고 계속 진행되도록 한다. 실패한 소스는 값으로 예외 객체를
    담아 반환하므로 호출부에서 소스별로 성공/실패를 구분해 처리할 수 있다.
    """
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        sources = ("weather", "country", "ip")
        results = await asyncio.gather(
            fetch_weather(client),
            fetch_country(client),
            fetch_ip_info(client),
            return_exceptions=True,
        )
    return dict(zip(sources, results, strict=True))
