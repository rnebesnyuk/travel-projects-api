import httpx


ARTIC_BASE = "https://api.artic.edu/api/v1"


class ArticError(Exception):
    """Raised when ArtIC API fails unexpectedly."""


async def artwork_exists(external_id: int) -> bool:
    url = f"{ARTIC_BASE}/artworks/{external_id}"
    timeout = httpx.Timeout(8.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, params={"fields": "id"})
        if resp.status_code == 200:
            return True
        if resp.status_code == 404:
            return False
        raise ArticError(f"ArtIC API error: {resp.status_code}")