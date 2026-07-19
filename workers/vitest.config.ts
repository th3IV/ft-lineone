import { defineConfig } from 'vitest/config';
import { defineWorkspace } from 'vitest/config';

export default defineWorkspace([
  // Unit tests for Workers
  {
    test: {
      name: 'workers',
      pool: 'cloudflare-workers',
      poolOptions: {
        workers: {
          wrangler: { configPath: './wrangler.jsonc' },
        },
      },
      environment: 'miniflare',
      include: ['tests/**/*.test.ts'],
      globals: true,
      testTimeout: 30000,
      hookTimeout: 10000,
    },
  },
  // Integration tests (Node.js)
  {
    test: {
      name: 'integration',
      pool: 'threads',
      environment: 'node',
      include: ['tests/integration/**/*.test.ts'],
      globals: true,
      testTimeout: 60000,
      hookTimeout: 30000,
    },
  },
]);

export default defineConfig({
  test: {
    globals: true,
    testTimeout: 30000,
    hookTimeout: 10000,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'tests/**',
        '**/*.d.ts',
        'dist/**',
        'node_modules/**',
      ],
    },
  },
});