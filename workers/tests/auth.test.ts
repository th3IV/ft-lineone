import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  create_access_token,
  create_refresh_token,
  verify_token,
  hash_password,
  verify_password,
  _b64url_encode,
  _b64url_decode,
} from '../src/services/auth';

// Mock environment
const mockEnv = {
  JWT_SECRET: 'test-secret-key-for-testing-only-32-bytes-long!!',
};

describe('Auth Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Base64 URL encoding/decoding', () => {
    it('should encode and decode correctly', () => {
      const data = Buffer.from('hello world');
      const encoded = _b64url_encode(data);
      const decoded = _b64url_decode(encoded);
      expect(decoded).toEqual(data);
    });

    it('should handle special characters', () => {
      const data = Buffer.from('hello+world/with=equals');
      const encoded = _b64url_encode(data);
      expect(encoded).not.toContain('+');
      expect(encoded).not.toContain('/');
      expect(encoded).not.toContain('=');
      const decoded = _b64url_decode(encoded);
      expect(decoded).toEqual(data);
    });

    it('should handle empty data', () => {
      const data = Buffer.from('');
      const encoded = _b64url_encode(data);
      const decoded = _b64url_decode(encoded);
      expect(decoded).toEqual(data);
    });
  });

  describe('JWT token creation', () => {
    it('should create access token with correct structure', () => {
      const token = create_access_token('user-123', 'test@example.com', undefined, { JWT_SECRET: 'test-secret' });

      expect(token).toBeDefined();
      expect(typeof token).toBe('string');

      const parts = token.split('.');
      expect(parts).toHaveLength(3);

      // Decode header
      const header = JSON.parse(Buffer.from(parts[0], 'base64url').toString());
      expect(header.alg).toBe('HS256');
      expect(header.typ).toBe('JWT');

      // Decode payload
      const payload = JSON.parse(Buffer.from(parts[1], 'base64url').toString());
      expect(payload.sub).toBe('user-123');
      expect(payload.email).toBe('test@example.com');
      expect(payload.type).toBe('access');
      expect(payload.jti).toBeDefined();
      expect(payload.exp).toBeGreaterThan(Date.now() / 1000);
    });

    it('should create refresh token with correct structure', () => {
      const token = create_refresh_token('user-123', 'test@example.com', { JWT_SECRET: 'test-secret' });

      expect(token).toBeDefined();
      const parts = token.split('.');
      expect(parts).toHaveLength(3);

      const payload = JSON.parse(Buffer.from(parts[1], 'base64url').toString());
      expect(payload.type).toBe('refresh');
      expect(payload.exp).toBeGreaterThan(Date.now() / 1000 + 29 * 24 * 60 * 60); // ~30 days
    });

    it('should create different tokens for same user', () => {
      const token1 = create_access_token('user-123', 'test@example.com', undefined, { JWT_SECRET: 'test-secret' });
      const token2 = create_access_token('user-123', 'test@example.com', undefined, { JWT_SECRET: 'test-secret' });

      expect(token1).not.toBe(token2); // Different JTI
    });
  });

  describe('JWT token verification', () => {
    it('should verify valid access token', () => {
      const token = create_access_token('user-123', 'test@example.com', undefined, { JWT_SECRET: 'test-secret' });
      const result = verify_token(token, 'access', { JWT_SECRET: 'test-secret' });

      expect(result).not.toBeNull();
      expect(result?.user_id).toBe('user-123');
      expect(result?.email).toBe('test@example.com');
      expect(result?.jti).toBeDefined();
    });

    it('should verify valid refresh token', () => {
      const token = create_refresh_token('user-123', 'test@example.com', { JWT_SECRET: 'test-secret' });
      const result = verify_token(token, 'refresh', { JWT_SECRET: 'test-secret' });

      expect(result).not.toBeNull();
      expect(result?.user_id).toBe('user-123');
      expect(result?.type).toBe('refresh');
    });

    it('should reject token with wrong type', () => {
      const token = create_access_token('user-123', 'test@example.com', undefined, { JWT_SECRET: 'test-secret' });
      const result = verify_token(token, 'refresh', { JWT_SECRET: 'test-secret' });
      expect(result).toBeNull();
    });

    it('should reject token with wrong secret', () => {
      const token = create_access_token('user-123', 'test@example.com', undefined, { JWT_SECRET: 'secret-1' });
      const result = verify_token(token, 'access', { JWT_SECRET: 'secret-2' });
      expect(result).toBeNull();
    });

    it('should reject malformed token', () => {
      const result = verify_token('invalid.token.here', 'access', { JWT_SECRET: 'secret' });
      expect(result).toBeNull();
    });

    it('should reject token with wrong algorithm', () => {
      // Create a token with RS256 header (should be rejected as we only accept HS256)
      const header = { alg: 'RS256', typ: 'JWT' };
      const payload = { sub: 'user-123', email: 'test@example.com', type: 'access' };
      const headerB64 = btoa(JSON.stringify(header)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
      const payloadB64 = btoa(JSON.stringify({ sub: 'user-123', email: 'test@example.com', type: 'access' })).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
      const token = `${headerB64}.${payloadB64}.signature`;

      const result = verify_token(token, 'access', { JWT_SECRET: 'test-secret' });
      expect(result).toBeNull();
    });

    it('should reject expired token', () => {
      // Create an expired token manually
      const header = { alg: 'HS256', typ: 'JWT' };
      const payload = {
        sub: 'user-123',
        email: 'test@example.com',
        exp: Math.floor(Date.now() / 1000) - 3600, // 1 hour ago
        iat: Math.floor(Date.now() / 1000) - 7200,
        type: 'access',
        jti: 'test-jti',
      };
      const headerB64 = btoa(JSON.stringify(header)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
      const payloadB64 = btoa(JSON.stringify({ ...payload })).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
      const signature = 'fake-signature';
      const token = `${headerB64}.${btoa(JSON.stringify({ ...payload, exp: Math.floor(Date.now() / 1000) - 3600 })).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')}.signature`;

      const result = verify_token(token, 'access', { JWT_SECRET: 'test-secret' });
      expect(result).toBeNull();
    });
  });

  describe('Password hashing', () => {
    it('should hash password with PBKDF2-SHA256', () => {
      const password = 'MySecurePassword123!';
      const hash = hash_password(password);

      expect(hash).toBeDefined();
      expect(hash.startsWith('260000:')).toBe(true);

      const parts = hash.split(':');
      expect(parts).toHaveLength(3);
      expect(parseInt(parts[0])).toBe(260000); // iterations
      expect(parts[1].length).toBe(32); // 16 bytes salt = 32 hex chars
      expect(parts[2].length).toBe(64); // 32 bytes hash = 64 hex chars
    });

    it('should verify correct password', () => {
      const password = 'MySecurePassword123!';
      const hash = hash_password(password);

      const result = verify_password(password, hash);
      expect(result).toBe(true);
    });

    it('should reject incorrect password', () => {
      const password = 'MySecurePassword123!';
      const wrongPassword = 'WrongPassword123!';
      const hash = hash_password(password);

      const result = verify_password(wrongPassword, hash);
      expect(result).toBe(false);
    });

    it('should produce different hashes for same password', () => {
      const password = 'MySecurePassword123!';
      const hash1 = hash_password(password);
      const hash2 = hash_password(password);

      expect(hash1).not.toBe(hash2); // Different salts
      expect(verify_password(password, hash1)).toBe(true);
      expect(verify_password(password, hash2)).toBe(true);
    });

    it('should reject legacy bcrypt format', () => {
      // bcrypt hashes start with $2a$, $2b$, or $2y$
      const legacyHash = '$2a$10$salt.hash';
      const result = verify_password('password', legacyHash);
      expect(result).toBe(false);
    });
  });

  describe('HMAC signing', () => {
    it('should produce consistent signatures', () => {
      const payload = Buffer.from('test payload');
      const secret = 'test-secret';

      const sig1 = _sign(payload, secret);
      const sig2 = _sign(payload, secret);

      expect(sig1).toBe(sig2);
    });

    it('should produce different signatures for different payloads', () => {
      const secret = 'test-secret';

      const sig1 = _sign(Buffer.from('payload 1'), secret);
      const sig2 = _sign(Buffer.from('payload 2'), secret);

      expect(sig1).not.toBe(sig2);
    });

    it('should produce different signatures for different secrets', () => {
      const payload = Buffer.from('test payload');

      const sig1 = _sign(payload, 'secret 1');
      const sig2 = _sign(payload, 'secret 2');

      expect(sig1).not.toBe(sig2);
    });
  });
});