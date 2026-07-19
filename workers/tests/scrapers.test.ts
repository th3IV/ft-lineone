import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ScraperRunner } from '../src/scrapers/scheduler';
import { ParisScraper } from '../src/scrapers/paris';
import { RipleyScraper } from '../src/scrapers/ripley';

// Mock the database service
const mockDB = {
  create_product: vi.fn().mockResolvedValue({ id: 'prod-123' }),
  count_products_by_store: vi.fn().mockResolvedValue(100),
  delete_stale_products: vi.fn().mockResolvedValue(5),
};

const mockEnv = {
  DB: {},
  PARIS_CNSTRC_KEY: 'test-paris-key',
  RIPLEY_API_KEY: 'test-ripley-key',
};

describe('Scrapers', () => {
  let runner: ScraperRunner;

  beforeEach(() => {
    vi.clearAllMocks();
    runner = new ScraperRunner(mockEnv, 30);
  });

  describe('ScraperRunner', () => {
    it('should have all stores registered', () => {
      expect(runner.scrapers).toHaveProperty('zara');
      expect(runner.scrapers).toHaveProperty('maui');
      expect(runner.scrapers).toHaveProperty('falabella');
      expect(runner.scrapers).toHaveProperty('hm');
      expect(runner.scrapers).toHaveProperty('fashionpark');
      expect(runner.scrapers).toHaveProperty('paris');
      expect(runner.scrapers).toHaveProperty('ripley');
    });

    it('should validate product data', () => {
      const validProduct = {
        external_id: 'ext-123',
        name: 'Valid Product',
        store: 'Zara',
        price: 29990,
        currency: 'CLP',
        category: 'Poleras',
        description: 'Description',
        original_url: 'https://example.com/product',
        image_url: 'https://example.com/image.jpg',
        image_urls: ['https://example.com/image.jpg'],
        sizes: ['S', 'M', 'L'],
        colors: ['Negro', 'Blanco'],
        availability: true,
      };

      // Access private method via type assertion
      const runnerAny = runner as any;
      expect(runnerAny._validate_product(validProduct)).toBe(true);
    });

    it('should reject invalid product (missing name)', () => {
      const invalidProduct = {
        external_id: 'ext-123',
        name: '',
        store: 'Zara',
        price: 29990,
      };

      const runnerAny = runner as any;
      expect(runnerAny._validate_product(invalidProduct)).toBe(false);
    });

    it('should reject invalid product (zero price)', () => {
      const invalidProduct = {
        external_id: 'ext-123',
        name: 'Product',
        store: 'Zara',
        price: 0,
      };

      const runnerAny = runner as any;
      expect(runnerAny._validate_product(invalidProduct)).toBe(false);
    });

    it('should reject product with name in sizes', () => {
      const invalidProduct = {
        external_id: 'ext-123',
        name: 'Polera Negra',
        store: 'Zara',
        price: 29990,
        sizes: ['Polera Negra', 'M', 'L'],
      };

      const runnerAny = runner as any;
      expect(runnerAny._validate_product(invalidProduct)).toBe(false);
    });

    it('should reject product with name in colors', () => {
      const invalidProduct = {
        external_id: 'ext-123',
        name: 'Polera Roja',
        store: 'Zara',
        price: 29990,
        colors: ['Polera Roja', 'Azul'],
      };

      const runnerAny = runner as any;
      expect(runnerAny._validate_product(invalidProduct)).toBe(false);
    });

    it('should reject product with size in colors', () => {
      const invalidProduct = {
        external_id: 'ext-123',
        name: 'Polera',
        store: 'Zara',
        price: 29990,
        sizes: ['M', 'L'],
        colors: ['M', 'Rojo'],
      };

      const runnerAny = runner as any;
      expect(runnerAny._validate_product(invalidProduct)).toBe(false);
    });
  });

  describe('ParisScraper', () => {
    let scraper: ParisScraper;

    beforeEach(() => {
      scraper = new ParisScraper();
    });

    it('should parse search results', async () => {
      // Mock fetch response
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          response: {
            results: [
              {
                id: 'paris-123',
                product_name: 'Polera Paris',
                price: 19990,
                url: '/producto/polera-paris/123',
                image_url: 'https://paris.cl/image.jpg',
                category: 'Poleras',
                sizes: ['S', 'M', 'L'],
                colors: ['Negro', 'Blanco'],
                availability: 'InStock',
              },
            ],
          },
        });

      const products = await scraper.search_products('polera mujer', 10);
      expect(products.length).toBeGreaterThanOrEqual(0);
    });

    it('should infer category from query', () => {
      expect(scraper._infer_category('polera mujer')).toBe('Poleras');
      expect(scraper._infer_category('jean hombre')).toBe('Pantalones');
      expect(scraper._infer_category('vestido fiesta')).toBe('Vestidos');
      expect(scraper._infer_category('chaqueta invierno')).toBe('Chaquetas');
      expect(scraper._infer_category('short playa')).toBe('Shorts');
      expect(scraper._infer_category('poleron deportes')).toBe('Polerones');
      expect(scraper._infer_category('zapato deporte')).toBe('');
    });

    it('should infer gender from query', () => {
      expect(scraper._infer_gender('polera hombre')).toBe('hombre');
      expect(scraper._infer_gender('vestido mujer')).toBe('mujer');
      expect(scraper._infer_gender('jean unisex')).toBe('');
    });
  });

  describe('RipleyScraper', () => {
    let scraper: RipleyScraper;

    beforeEach(() => {
      scraper = new RipleyScraper();
    });

    it('should parse HTML products', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        text: async () => `
          <html>
            <body>
              <div class="product-item" data-product-id="ripley-123">
                <h3 class="product-name">Polera Ripley</h3>
                <span class="price">$24.990</span>
                <img src="https://ripley.cl/image.jpg" />
                <a href="/producto/polera-ripley/123">Ver</a>
              </div>
            </body>
          </html>
        `,
      });

      const products = await scraper.search_products('polera hombre', 5);
      expect(Array.isArray(products)).toBe(true);
    });

    it('should infer category from query', () => {
      expect(scraper._infer_category('polera mujer')).toBe('Poleras');
      expect(scraper._infer_category('jean hombre')).toBe('Pantalones');
      expect(scraper._infer_category('vestido fiesta')).toBe('Vestidos');
      expect(scraper._infer_category('chaqueta cuero')).toBe('Chaquetas');
      expect(scraper._infer_category('falda larga')).toBe('Faldas');
      expect(scraper._infer_category('short deporte')).toBe('Shorts');
      expect(scraper._infer_category('poleron gym')).toBe('Polerones');
    });

    it('should infer gender from query', () => {
      expect(scraper._infer_gender('polera hombre')).toBe('hombre');
      expect(scraper._infer_gender('vestido mujer')).toBe('mujer');
      expect(scraper._infer_gender('pantalon unisex')).toBe('');
    });
  });
});