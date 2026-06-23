from typing import List, Dict, Any
from src.infrastructure.scrapers.base_scraper import BaseScraper
from src.infrastructure.scrapers.playwright_base import PlaywrightScraperHelper


class ZaraScraper(BaseScraper):
    CATEGORY_URLS = {
        "woman_tshirts": "/cl/es/mujer-camisetas-l1362.html",
        "woman_dresses": "/cl/es/mujer-vestidos-l1066.html",
        "woman_pants": "/cl/es/mujer-pantalones-l1335.html",
        "woman_jackets": "/cl/es/mujer-chaquetas-l1114.html",
        "man_tshirts": "/cl/es/hombre-camisetas-l855.html",
        "man_shirts": "/cl/es/hombre-camisas-l737.html",
        "man_pants": "/cl/es/hombre-pantalones-l838.html",
        "man_jackets": "/cl/es/hombre-chaquetas-l640.html",
    }

    def __init__(self):
        super().__init__("zara", "https://www.zara.com")
        self._pw = PlaywrightScraperHelper()

    async def scrape_category(self, category: str, max_items: int) -> List[Dict[str, Any]]:
        url_path = self.CATEGORY_URLS.get(category)
        if not url_path:
            return []

        url = f"{self.base_url}{url_path}"
        products = await self._extract_zara_products(url, max_items)

        for p in products:
            p["category"] = category
            p["currency"] = "CLP"

        return products

    async def _extract_zara_products(self, url: str, max_items: int) -> List[Dict[str, Any]]:
        await self._pw.start()

        page = await self._pw._context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)

            # Scroll to trigger lazy-loading of images
            await page.evaluate("""
                async () => {
                    const grid = document.querySelector('ul[class*="product-grid"]') || document.body;
                    const step = window.innerHeight * 0.8;
                    const totalHeight = grid.scrollHeight;
                    for (let y = 0; y < totalHeight; y += step) {
                        window.scrollTo(0, y);
                        await new Promise(r => setTimeout(r, 300));
                    }
                    window.scrollTo(0, 0);
                }
            """)
            await page.wait_for_timeout(2000)

            raw = await page.evaluate("""
                (max) => {
                    const products = [];
                    const items = document.querySelectorAll('li._product');

                    for (const item of items) {
                        const pid = item.getAttribute('data-productid');
                        const link = item.querySelector('a.product-link');
                        const href = link ? link.getAttribute('href') : '';
                        const img = item.querySelector('img');
                        let imgSrc = img ? (img.getAttribute('src') || img.getAttribute('data-src') || '') : '';

                        // Skip transparent placeholders
                        if (imgSrc.includes('transparent-background')) {
                            imgSrc = '';
                        }

                        if (!pid || !href) continue;

                        // Try inline name/price first
                        let nameEl = item.querySelector('h3');
                        let name = nameEl ? nameEl.textContent.trim() : '';
                        let priceEl = item.querySelector('data[data-currency]');
                        let price = priceEl ? parseFloat(priceEl.getAttribute('value')) : 0;

                        // Fallback: parallel dynamic grid (match by URL)
                        if (!name || price <= 0) {
                            const infoItem = document.querySelector(
                                'li.product-grid-block-dynamic__product-info a.product-link[href="' + href + '"]'
                            );
                            if (infoItem) {
                                const infoParent = infoItem.closest('li');
                                nameEl = infoParent ? infoParent.querySelector('h3') : null;
                                name = nameEl ? nameEl.textContent.trim() : name;
                                priceEl = infoParent ? infoParent.querySelector('data[data-currency]') : null;
                                price = priceEl ? parseFloat(priceEl.getAttribute('value')) : price;
                            }
                        }

                        if (name && price > 0) {
                            products.push({
                                external_id: 'zar-' + pid,
                                name: name,
                                price: price,
                                currency: 'CLP',
                                image_url: imgSrc || '',
                                product_url: href,
                            });
                        }

                        if (products.length >= max) break;
                    }
                    return products;
                }
            """, max_items)

            return raw
        finally:
            await page.close()

    async def close(self):
        await self._pw.close()
        await super().close()
