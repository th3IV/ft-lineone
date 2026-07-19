import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DatabaseService } from '../src/services/database';

// Mock D1 database
const mockDB = {
  prepare: vi.fn(() => ({
    bind: vi.fn().mockReturnThis(),
    first: vi.fn().mockResolvedValue(null),
    all: vi.fn().mockResolvedValue({ results: [] }),
    run: vi.fn().mockResolvedValue({ changes: 0 }),
  })),
};

const mockEnv = {
  DB: mockDB,
  R2: {
    put: vi.fn().mockResolvedValue(undefined),
    get: vi.fn().mockResolvedValue(null),
    delete: vi.fn().mockResolvedValue(undefined),
  },
  AI: {
    run: vi.fn().mockResolvedValue({ response: 'test' }),
  },
};

describe('DatabaseService', () => {
  let db: DatabaseService;

  beforeEach(() => {
    vi.clearAllMocks();
    db = new DatabaseService(mockEnv);
  });

  describe('User Management', () => {
    it('should create user', async () => {
      const mockPrepare = mockDB.prepare as vi.Mock;
      mockPrepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        run: vi.fn().mockResolvedValue({ success: true }),
      }));

      const user = await db.create_user({
        email: 'test@example.com',
        name: 'Test User',
        password_hash: 'hashed-password',
      });

      expect(user).toBeDefined();
      expect(user.email).toBe('test@example.com');
      expect(user.name).toBe('Test User');
    });

    it('should get user by email', async () => {
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        password_hash: 'hashed',
        is_premium: 0,
        plan_type: 'free',
        created_at: new Date().toISOString(),
      };

      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        first: vi.fn().mockResolvedValue(mockUser),
      });

      const user = await db.get_user_by_email('test@example.com');
      expect(user).toBeDefined();
      expect(user?.email).toBe('test@example.com');
    });

    it('should return null for non-existent user', async () => {
      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        first: vi.fn().mockResolvedValue(null),
      });

      const user = await db.get_user_by_email('nonexistent@example.com');
      expect(user).toBeNull();
    });
  });

  describe('Product Management', () => {
    it('should create product', async () => {
      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        run: vi.fn().mockResolvedValue({ success: true }),
      });

      const product = await db.create_product({
        external_id: 'ext-123',
        name: 'Test Product',
        store: 'Zara',
        price: 29990,
        currency: 'CLP',
        category: 'Poleras',
        description: 'Test description',
        original_url: 'https://example.com/product',
        image_url: 'https://example.com/image.jpg',
        image_urls: ['https://example.com/image.jpg'],
        sizes: ['S', 'M', 'L'],
        colors: ['Negro', 'Blanco'],
        availability: true,
      });

      expect(product).toBeDefined();
      expect(product.name).toBe('Test Product');
      expect(product.store).toBe('Zara');
    });

    it('should get products with filters', async () => {
      const mockProducts = [
        {
          id: 'prod-1',
          external_id: 'ext-1',
          name: 'Product 1',
          store: 'Zara',
          price: 29990,
          currency: 'CLP',
          category: 'Poleras',
          description: 'Desc 1',
          original_url: 'https://example.com/1',
          image_url: 'https://example.com/img1.jpg',
          image_urls: '["https://example.com/img1.jpg"]',
          sizes: '["S","M"]',
          colors: '["Negro"]',
          availability: 1,
          created_at: new Date().toISOString(),
        },
      ];

      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        all: vi.fn().mockResolvedValue({ results: mockProducts }),
      });

      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        first: vi.fn().mockResolvedValue({ total: 1 }),
      });

      const [products, total] = await db.get_products({ store: 'Zara' }, 1, 20);
      expect(products).toHaveLength(1);
      expect(total).toBe(1);
    });

    it('should upsert product on conflict', async () => {
      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        run: vi.fn().mockResolvedValue({ success: true }),
      });

      const product = await db.create_product({
        external_id: 'ext-123',
        name: 'Updated Product',
        store: 'Zara',
        price: 39990,
        currency: 'CLP',
        category: 'Poleras',
        description: 'Updated description',
        original_url: 'https://example.com/product',
        image_url: 'https://example.com/image.jpg',
        image_urls: ['https://example.com/image.jpg'],
        sizes: ['M', 'L'],
        colors: ['Azul'],
        availability: true,
      });

      expect(product.name).toBe('Updated Product');
      expect(product.price).toBe(39990);
    });
  });

  describe('Usage Limits', () => {
    it('should check usage limits', async () => {
      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        first: vi.fn().mockResolvedValue({ vton_count: 3, llm_count: 2 }),
      });

      const result = await db.can_use_feature('user-123', 'vton');
      expect(result.allowed).toBe(true);
      expect(result.current).toBe(3);
      expect(result.limit).toBe(5);
    });

    it('should deny when limit exceeded', async () => {
      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        first: vi.fn().mockResolvedValue({ vton_count: 5, llm_count: 0 }),
      });

      const result = await db.can_use_feature('user-123', 'vton');
      expect(result.allowed).toBe(false);
      expect(result.current).toBe(5);
      expect(result.limit).toBe(5);
    });

    it('should allow unlimited for premium users', async () => {
      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        first: vi.fn().mockResolvedValue({ is_premium: 1, plan_type: 'premium' }),
      });

      const result = await db.can_use_feature('user-123', 'vton');
      expect(result.allowed).toBe(true);
      expect(result.limit).toBe(-1);
    });
  });

  describe('VTON Results', () => {
    it('should create VTON result', async () => {
      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        run: vi.fn().mockResolvedValue({ success: true }),
      });

      const result = await db.create_vton_result({
        user_id: 'user-123',
        product_id: 'prod-456',
        status: 'pending',
        input_image_url: 'https://example.com/input.jpg',
        garment_image_url: 'https://example.com/garment.jpg',
        youcam_task_id: 'task-123',
      });

      expect(result).toBeDefined();
      expect(result.user_id).toBe('user-123');
      expect(result.status).toBe('pending');
    });

    it('should get VTON history', async () => {
      const mockHistory = [
        {
          id: 'vton-1',
          user_id: 'user-123',
          product_id: 'prod-1',
          status: 'completed',
          input_image_url: 'https://example.com/in.jpg',
          output_image_url: 'https://example.com/out.jpg',
          error_message: null,
          youcam_task_id: 'task-1',
          created_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
        },
      ];

      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        all: vi.fn().mockResolvedValue({ results: mockHistory }),
      });

      const history = await db.get_vton_history('user-123', 20);
      expect(history).toHaveLength(1);
      expect(history[0].status).toBe('completed');
    });
  });

  describe('Favorites', () => {
    it('should add favorite', async () => {
      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        run: vi.fn().mockResolvedValue({ success: true }),
      });

      await db.add_favorite('user-123', 'prod-456');
      expect(mockDB.prepare).toHaveBeenCalled();
    });

    it('should check if product is favorite', async () => {
      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        first: vi.fn().mockResolvedValue({ id: 'fav-1' }),
      });

      const isFav = await db.is_favorite('user-123', 'prod-456');
      expect(isFav).toBe(true);
    });

    it('should remove favorite', async () => {
      mockDB.prepare.mockImplementationOnce(() => ({
        bind: vi.fn().mockReturnThis(),
        run: vi.fn().mockResolvedValue({ success: true }),
      });

      await db.remove_favorite('user-123', 'prod-456');
      expect(mockDB.prepare).toHaveBeenCalled();
    });
  });
});