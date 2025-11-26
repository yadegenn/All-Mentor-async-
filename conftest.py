import asyncio
import pytest

@pytest.fixture(scope="session")
def event_loop(request):
    """
    Создает экземпляр цикла событий по умолчанию для всего сеанса тестирования.
    Это принудительно активирует режим asyncio для pytest.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()