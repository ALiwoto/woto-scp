import httpx


class AsfClient:
    authentication: str = None
    base_url: str = None
    http_client: 'httpx.AsyncClient' = None

    def __init__(self, base_url: str, password: str) -> None:
        self.base_url = base_url
        self.authentication = password
        self.http_client = httpx.AsyncClient()
    
    async def close(self) -> None:
        await self.http_client.aclose()
    
    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        return await self.http_client.get(
            f'{self.base_url}/{endpoint}',
            headers={'Authorization': self.authentication},
            **kwargs
        )
    
    async def post(self, endpoint: str, **kwargs) -> httpx.Response:
        return await self.http_client.post(
            f'{self.base_url}/{endpoint}',
            headers={'Authorization': self.authentication},
            **kwargs
        )
    

