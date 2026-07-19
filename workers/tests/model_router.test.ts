import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ModelRouter, TaskType, ModelType } from '../src/services/model_router';

// Mock environment
const mockEnv = {
  AI: {
    run: vi.fn().mockResolvedValue({ response: 'test response' }),
    run_stream: vi.fn().mockImplementation(async function* () {
      yield { content: 'Hello' };
      yield { content: ' world' };
    }),
  };

describe('ModelRouter', () => {
  let router: ModelRouter;

  beforeEach(() => {
    vi.clearAllMocks();
    router = new ModelRouter(mockEnv);
  });

  describe('Model Selection', () => {
    it('should select Moondream for vision precheck', () => {
      const model = router._get_model('vision_precheck', false);
      expect(model).toBe('@cf/moondream/moondream3.1-9B-A2B');

      const modelPremium = router._get_model('vision_precheck', true);
      expect(modelPremium).toBe('@cf/moondream/moondream3.1-9B-A2B');
    });

    it('should select DeepSeek R1 for premium reasoning', () => {
      const model = router._get_model('reasoning_premium', true);
      expect(model).toBe('@cf/deepseek/deepseek-r1-distill-qwen-32b');
    });

    it('should fallback to Llama 4 Scout for free user reasoning', () => {
      const model = router._get_model('reasoning_premium', false);
      expect(model).toBe('@cf/meta/llama-4-scout-17b-16e-instruct');
    });

    it('should select Llama 4 Scout for premium chat', () => {
      const model = router._get_model('chat_general', true);
      expect(model).toBe('@cf/meta/llama-4-scout-17b-16e-instruct');
    });

    it('should select Llama 3.3 70B for free chat', () => {
      const model = router._get_model('chat_general', false);
      expect(model).toBe('@cf/meta/llama-3.3-70b-instruct-fp8-fast');
    });

    it('should select Llama 4 Scout for premium recommendations', () => {
      const model = router._get_model('recommendations', true);
      expect(model).toBe('@cf/meta/llama-4-scout-17b-16e-instruct');
    });

    it('should select Llama 3.3 70B for free recommendations', () => {
      const model = router._get_model('recommendations', false);
      expect(model).toBe('@cf/meta/llama-3.3-70b-instruct-fp8-fast');
    });

    it('should select Llama 3.2 3B for fast chat', () => {
      const model = router._get_model('fast_chat', true);
      expect(model).toBe('@cf/meta/llama-3.2-3b-instruct');

      const modelFree = router._get_model('fast_chat', false);
      expect(modelFree).toBe('@cf/meta/llama-3.2-3b-instruct');
    });

    it('should select BGE-M3 for embeddings', () => {
      const model = router._get_model('embedding', true);
      expect(model).toBe('@cf/baai/bge-m3');

      const modelFree = router._get_model('embedding', false);
      expect(modelFree).toBe('@cf/baai/bge-m3');
    });

    it('should default to Llama 4 Scout for unknown tasks', () => {
      const model = router._get_model('unknown_task', false);
      expect(model).toBe('@cf/meta/llama-4-scout-17b-16e-instruct');
    });
  });

  describe('Streaming Support', () => {
    it('should identify streaming-capable models', () => {
      expect(router._supports_streaming('@cf/meta/llama-4-scout-17b-16e-instruct')).toBe(true);
      expect(router._supports_streaming('@cf/deepseek/deepseek-r1-distill-qwen-32b')).toBe(true);
      expect(router._supports_streaming('@cf/meta/llama-3.3-70b-instruct-fp8-fast')).toBe(true);
      expect(router._supports_streaming('@cf/deepseek/deepseek-r1-distill-qwen-32b')).toBe(true);
      expect(router._supports_streaming('@cf/meta/llama-3.2-3b-instruct')).toBe(true);
    });

    it('should identify non-streaming models', () => {
      expect(router._supports_streaming('@cf/moondream/moondream3.1-9B-A2B')).toBe(false);
    });
  });

  describe('Vision Support', () => {
    it('should identify vision-capable models', () => {
      expect(router._supports_vision('@cf/moondream/moondream3.1-9B-A2B')).toBe(true);
    });

    it('should identify non-vision models', () => {
      expect(router._supports_vision('@cf/meta/llama-4-scout-17b-16e-instruct')).toBe(false);
      expect(router._supports_vision('@cf/deepseek/deepseek-r1-distill-qwen-32b')).toBe(false);
    });
  });

  describe('Run Inference', () => {
    it('should call AI.run with correct parameters for chat', async () => {
      const result = await router.run({
        task_type: 'chat_general',
        messages: [
          { role: 'system', content: 'You are helpful' },
          { role: 'user', content: 'Hello' },
        ],
        is_premium: false,
        max_tokens: 512,
        temperature: 0.7,
      });

      expect(mockEnv.AI.run).toHaveBeenCalledWith(
        '@cf/meta/llama-3.3-70b-instruct-fp8-fast',
        expect.objectContaining({
          messages: expect.arrayContaining([
            expect.objectContaining({ role: 'system' }),
            expect.objectContaining({ role: 'user', content: 'Hello' }),
          ]),
          max_tokens: 512,
          temperature: 0.7,
        })
      );
      expect(result).toEqual({ response: 'test response' });
    });

    it('should use premium model for premium users', async () => {
      await router.run({
        task_type: 'chat_general',
        messages: [{ role: 'user', content: 'Hello' }],
        is_premium: true,
      });

      expect(mockEnv.AI.run).toHaveBeenCalledWith(
        '@cf/meta/llama-4-scout-17b-16e-instruct',
        expect.any(Object)
      );
    });

    it('should use Moondream for vision precheck', async () => {
      await router.run({
        task_type: 'vision_precheck',
        messages: [{
          role: 'user',
          content: [
            { type: 'image_url', image_url: 'https://example.com/image.jpg' },
            { type: 'text', text: 'Is there a person?' }
          ]
        }],
        is_premium: true,
      });

      expect(mockEnv.AI.run).toHaveBeenCalledWith(
        '@cf/moondream/moondream3.1-9B-A2B',
        expect.objectContaining({
          messages: expect.arrayContaining([
            expect.objectContaining({
              content: expect.arrayContaining([
                expect.objectContaining({ type: 'image_url' }),
                expect.objectContaining({ type: 'text' }),
              ])
            })
          ]
        })
      );
    });

    it('should use DeepSeek R1 for premium reasoning', async () => {
      await router.run({
        task_type: 'reasoning_premium',
        messages: [{ role: 'user', content: 'Solve this complex problem' }],
        is_premium: true,
      });

      expect(mockEnv.AI.run).toHaveBeenCalledWith(
        '@cf/deepseek/deepseek-r1-distill-qwen-32b',
        expect.objectContaining({
          messages: expect.arrayContaining([
            expect.objectContaining({ role: 'user', content: 'Solve this complex problem' })
          ])
        })
      );
    });

    it('should fallback to Llama 4 Scout for free user reasoning', async () => {
      await router.run({
        task_type: 'reasoning_premium',
        messages: [{ role: 'user', content: 'Solve this' }],
        is_premium: false,
      });

      expect(mockEnv.AI.run).toHaveBeenCalledWith(
        '@cf/meta/llama-4-scout-17b-16e-instruct',
        expect.any(Object)
      );
    });

    it('should handle embedding task', async () => {
      mockEnv.AI.run.mockResolvedValueOnce({ data: [[0.1, 0.2, 0.3]] });

      const embeddings = await router.embed(['text 1', 'text 2']);

      expect(mockEnv.AI.run).toHaveBeenCalledWith(
        '@cf/baai/bge-m3',
        { text: ['text 1', 'text 2'] }
      );
      expect(embeddings).toEqual([[0.1, 0.2, 0.3]]);
    });

    it('should handle vision check', async () => {
      mockEnv.AI.run.mockResolvedValueOnce({ answer: 'yes' });

      const result = await router.vision_check(
        'https://example.com/image.jpg',
        'Is there a person?'
      );

      expect(result).toEqual({
        has_body: true,
        confidence: 0.9,
        details: 'yes',
      });
    });

    it('should extract content from various response formats', () => {
      // Test choices format (new format)
      let result = router._extract_content({ choices: [{ message: { content: 'Hello' } }] });
      expect(result).toBe('Hello');

      // Test old format
      result = router._extract_content({ response: 'Old format' });
      expect(result).toBe('Old format');

      // Test choices format (new format)
      result = router._extract_content({ choices: [{ message: { content: 'New format' } }] });
      expect(result).toBe('New format');

      // Test JSON string with advice
      result = router._extract_content('{"advice": "JSON advice", "products": []}');
      expect(result).toBe('{"advice": "JSON advice", "products": []}');

      // Test empty result
      result = router._extract_content(null);
      expect(result).toBe('');

      // Test empty object
      result = router._extract_content({});
      expect(result).toBe('');
    });
  });

  describe('Error Handling', () => {
    it('should handle AI errors gracefully', async () => {
      mockEnv.AI.run.mockRejectedValueOnce(new Error('AI service unavailable'));

      await expect(router.run({
        task_type: 'chat_general',
        messages: [{ role: 'user', content: 'Hello' }],
        is_premium: false,
      }).rejects.toThrow('AI service unavailable');
    });

    it('should handle invalid model response', async () => {
      mockEnv.AI.run.mockResolvedValueOnce(null);

      const result = await router.run({
        task_type: 'chat_general',
        messages: [{ role: 'user', content: 'Hello' }],
        is_premium: false,
      });

      expect(result).toBeNull();
    });
  });
});