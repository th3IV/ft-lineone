import { describe, it, expect, vi, beforeEach } from 'vitest';
import { verify_turnstile, TurnstileService } from '../src/services/turnstile';

describe('Turnstile Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('verify_turnstile', () => {
    it('should reject missing token', async () => {
      const result = await verify_turnstile('', 'secret-key');
      expect(result.success).toBe(false);
      expect(result.error_codes).toContain('missing-input');
    });

    it('should reject missing secret', async () => {
      const result = await verify_turnstile('token', '');
      expect(result.success).toBe(false);
      expect(result.error_codes).toContain('missing-secret');
    });

    it('should call Cloudflare API', async () => {
      const mockFetch = vi.spyOn(global, 'fetch').mockResolvedValue({
        ok: true,
        text: async () => JSON.stringify({
          success: true,
          challenge_ts: '2024-01-01T00:00:00Z',
          hostname: 'example.com',
        }),
      });

      const result = await verify_turnstile('valid-token', 'secret-key', '192.168.1.1');

      expect(result.success).toBe(true);
      expect(result.error_codes).toEqual([]);
      expect(global.fetch).toHaveBeenCalledWith(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'secret=secret-key&response=valid-token&remoteip=192.168.1.1',
        })
      );

      mockFetch.mockRestore();
    });

    it('should handle API error response', async () => {
      const mockFetch = vi.spyOn(global, 'fetch').mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => 'Internal Server Error',
      });

      const result = await verify_turnstile('token', 'secret');

      expect(result.success).toBe(false);
      expect(result.error_codes).toContain('internal-error');

      mockFetch.mockRestore();
    });

    it('should handle network error', async () => {
      const mockFetch = vi.spyOn(global, 'fetch').mockRejectedValue(new Error('Network error'));

      const result = await verify_turnstile('token', 'secret');

      expect(result.success).toBe(false);
      expect(result.error_codes).toContain('internal-error');

      mockFetch.mockRestore();
    });
  });

  describe('TurnstileService', () => {
    let service: any;
    const mockEnv = {
      TURNSTILE_SECRET_KEY: 'test-secret',
      TURNSTILE_SITE_KEY: 'test-site-key',
      ENVIRONMENT: 'development',
    };

    beforeEach(() => {
      vi.clearAllMocks();
      service = new (await import('../src/services/turnstile')).TurnstileService(mockEnv);
    });

    it('should create service with env bindings', () => {
      expect(service.secret_key).toBe('test-secret');
      expect(service.site_key).toBe('test-site-key');
    });

    it('should allow unverified in development', async () => {
      const devEnv = { ...mockEnv, ENVIRONMENT: 'development' };
      const devService = new (await import('../src/services/turnstile')).TurnstileService(devEnv);

      const result = await devService.verify('any-token');
      expect(result.success).toBe(true);
      expect(result.error_codes).toEqual([]);
    });

    it('should require secret in production', async () => {
      const prodEnv = {
        ...mockEnv,
        ENVIRONMENT: 'production',
        TURNSTILE_SECRET_KEY: '',
      };
      const prodService = new (await import('../src/services/turnstile')).TurnstileService(prodEnv);

      const result = await prodService.verify('token');
      expect(result.success).toBe(false);
      expect(result.error_codes).toContain('server-config');
    });

    it('should verify valid token', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        text: async () => JSON.stringify({
          success: true,
          challenge_ts: '2024-01-01T00:00:00Z',
          hostname: 'example.com',
        }),
      });

      const result = await service.verify('valid-token', '192.168.1.1');

      expect(result.success).toBe(true);
      expect(result.hostname).toBe('example.com');
      expect(global.fetch).toHaveBeenCalledWith(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'secret=test-secret&response=valid-token&remoteip=192.168.1.1',
        })
      );
    });

    it('should handle invalid token', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        text: async () => JSON.stringify({
          success: false,
          'error-codes': ['invalid-input-response'],
        }),
      });

      const result = await service.verify('invalid-token');

      expect(result.success).toBe(false);
      expect(result.error_codes).toContain('invalid-input-response');
    });

    it('should get site key for frontend', () => {
      const siteKey = service.get_site_key();
      expect(siteKey).toBe('test-site-key');
    });
  });
});