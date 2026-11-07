"""Спільні налаштування тестів застосунку: позначки рівнів тестів."""


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: потребує Docker (PostgreSQL у Testcontainers)"
    )
    config.addinivalue_line("markers", "e2e: потребує браузера (Playwright)")
