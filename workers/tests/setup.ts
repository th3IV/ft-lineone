import { beforeAll, afterAll, vi } from 'vitest';

// Mock Cloudflare bindings for testing
globalThis.env = {
  DB: {
    prepare: vi.fn(() => ({
      bind: vi.fn().mockReturnThis(),
      first: vi.fn().mockResolvedValue(null),
      all: vi.fn().mockResolvedValue({ results: [] }),
      run: vi.fn().mockResolvedValue({ changes: 0 }),
    })),
  },
  R2: {
    put: vi.fn().mockResolvedValue(undefined),
    get: vi.fn().mockResolvedValue(null),
    delete: vi.fn().mockResolvedValue(undefined),
  },
  AI: {
    run: vi.fn().mockResolvedValue({ response: 'test response' }),
  },
  VECTORIZE: {
    upsert: vi.fn().mockResolvedValue(undefined),
    query: vi.fn().mockResolvedValue({ matches: [] }),
    delete: vi.fn().mockResolvedValue(undefined),
  },
  SCRAPER_QUEUE: {
    send: vi.fn().mockResolvedValue(undefined),
  },
  PREMIUM_KV: {
    get: vi.fn().mockResolvedValue(null),
    put: vi.fn().mockResolvedValue(undefined),
    delete: vi.fn().mockResolvedValue(undefined),
  },
  JWT_SECRET: 'test-secret-key-for-testing-only',
  TRANSBANK_API_KEY: 'test-transbank-key',
  TRANSBANK_BASE_URL: 'https://webpay3gint.transbank.cl',
  TRANSBANK_COMMERCE_CODE: '597055555532',
  TRANSBANK_RETURN_URL: 'https://thelineone.com/payment/success',
  YOUCAM_API_KEY: 'test-youcam-key',
  YOUCAM_WEBHOOK_SECRET: 'test-webhook-secret',
  TURNSTILE_SECRET_KEY: 'test-turnstile-secret',
  TURNSTILE_SITE_KEY: 'test-turnstile-site-key',
  ENVIRONMENT: 'test',
  CLOUDFLARE_AI_GATEWAY_ID: 'test-gateway',
  TRANSBANK_COMMERCE_CODE: '597055555532',
  TRANSBANK_BASE_URL: 'https://webpay3gint.transbank.cl',
  TRANSBANK_RETURN_URL: 'https://thelineone.com/payment/success',
  ADMIN_EMAILS: 'test@example.com',
  CORS_ORIGINS: 'https://thelineone.com,https://www.thelineone.com,http://localhost:3000',
  JWT_ALGORITHM: 'EdDSA',
  CLOUDFLARE_AI_GATEWAY_ID: 'ft-lineone-vton',
  JWT_ALGORITHM: 'EdDSA',
};

// Mock JS modules for Pyodide
globalThis.js = {
  fetch: vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    text: vi.fn().mockResolvedValue('{}'),
    json: vi.fn().mockResolvedValue({}),
    arrayBuffer: vi.fn().mockResolvedValue(new ArrayBuffer(0)),
  }),
  AbortController: vi.fn(() => ({
    signal: {},
    abort: vi.fn(),
  })),
  setTimeout: vi.fn((fn, ms) => setTimeout(fn, ms)),
  Uint8Array: globalThis.Uint8Array,
};

globalThis.Response = class MockResponse {
  constructor(body, init) {
    this.body = body;
    this.status = init?.status || 200;
    this.statusText = init?.statusText || 'OK';
    this.headers = new Headers(init?.headers);
  }
  static json(data, init) {
    const res = new MockResponse(JSON.stringify(data), {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    });
    return res;
  }
  async text() { return this.body; }
  async json() { return JSON.parse(this.body); }
}

globalThis.Request = class MockRequest {
  constructor(url, init) {
    this.url = url;
    this.method = init?.method || 'GET';
    this.headers = new Headers(init?.headers);
    this.body = init?.body;
  }
  async text() { return this.body || ''; }
  async json() { return JSON.parse(this.body || '{}'); }
}

globalThis.Headers = class MockHeaders {
  constructor(init) {
    this._map = new Map();
    if (init) {
      if (init instanceof Headers) {
        init.forEach((v, k) => this._map.set(k.toLowerCase(), v));
      } else if (Array.isArray(init)) {
        init.forEach(([k, v]) => this._map.set(k.toLowerCase(), v));
      } else if (typeof init === 'object') {
        Object.entries(init).forEach(([k, v]) => this._map.set(k.toLowerCase(), v));
      }
    }
  }
  get(key) { return this._map.get(key.toLowerCase()); }
  set(key, value) { this._map.set(key.toLowerCase(), value); }
  has(key) { return this._map.has(key.toLowerCase()); }
  delete(key) { this._map.delete(key.toLowerCase()); }
  forEach(fn) { this._map.forEach((v, k) => fn(v, k, this)); }
  keys() { return this._map.keys(); }
  values() { return this._map.values(); }
  entries() { return this._map.entries(); }
}

// Mock crypto for Ed25519
globalThis.crypto = {
  subtle: {
    importKey: vi.fn().mockResolvedValue({}),
    sign: vi.fn().mockResolvedValue(new ArrayBuffer(64)),
    verify: vi.fn().mockResolvedValue(true),
    generateKey: vi.fn().mockResolvedValue({ privateKey: {}, publicKey: {} }),
    exportKey: vi.fn().mockResolvedValue(new ArrayBuffer(32)),
  },
  getRandomValues: (arr) => {
    for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 256);
    return arr;
  },
  randomUUID: () => 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  }),
};

// Mock TextEncoder/Decoder
globalThis.TextEncoder = class TextEncoder {
  encode(str) { return new TextEncoder().encode(str); }
}
globalThis.TextDecoder = class TextDecoder {
  decode(bytes) { return new TextDecoder().decode(bytes); }
}

// Mock console methods for cleaner test output
const originalConsole = { ...console };
beforeAll(() => {
  console.log = vi.fn();
  console.warn = vi.fn();
  console.error = vi.fn();
});

afterAll(() => {
  console.log = originalConsole.log;
  console.warn = originalConsole.warn;
  console.error = originalConsole.error;
});

// Helper functions for tests
export function createMockEnv(overrides = {}) {
  return {
    ...globalThis.env,
    ...overrides,
  };
}

export function createMockRequest(overrides = {}) {
  return new Request('https://api.thelineone.com/api/v1/test', {
    method: overrides.method || 'GET',
    headers: overrides.headers || {},
    body: overrides.body,
  });
}

export function createMockResponse(body, init = {}) {
  return new Response(body, init);
}