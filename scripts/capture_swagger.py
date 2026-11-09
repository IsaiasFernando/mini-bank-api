"""Capture real screenshots of the running Swagger UI for the README.

Usage:
    pip install playwright
    playwright install chromium
    uvicorn app.main:app --reload
    python scripts/capture_swagger.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000/docs"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "images"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        response = page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
        if response is None or response.status >= 400:
            browser.close()
            raise SystemExit(f"Não foi possível abrir {BASE_URL}. Inicie a API e tente novamente.")
        page.locator(".swagger-ui").wait_for(state="visible", timeout=20_000)
        page.screenshot(path=OUTPUT_DIR / "swagger-overview.png", full_page=True)
        for endpoint in ("/auth/login", "/accounts/me/deposit", "/accounts/me/withdraw", "/transfers", "/accounts/me/statement"):
            summaries = page.locator(".opblock-summary")
            for index in range(summaries.count()):
                summary = summaries.nth(index)
                if endpoint in (summary.inner_text() or ""):
                    summary.scroll_into_view_if_needed()
                    summary.click()
                    break
        page.screenshot(path=OUTPUT_DIR / "swagger-auth-and-banking.png", full_page=True)
        browser.close()
    print(f"Capturas salvas em: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
