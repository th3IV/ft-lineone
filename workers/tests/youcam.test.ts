import { describe, it, expect, vi, beforeEach } from 'vitest';
import { YouCamService } from '../src/services/youcam';

// Mock environment
const mockEnv = {
  YOUCAM_API_KEY: 'test-youcam-api-key',
};

describe('YouCamService', () => {
  let service: YouCamService;

  beforeEach(() => {
    vi.clearAllMocks();
    service = new YouCamService(mockEnv);
  });

  describe('create_task', () => {
    it('should create a VTON task successfully', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: () => Promise.resolve(JSON.stringify({
          data: { task_id: 'task-12345' }
        })),
      };

      global.fetch = vi.fn().mockResolvedValue(mockResponse);

      const taskId = await service.create_task(
        'https://example.com/user.jpg',
        'https://example.com/garment.jpg',
        'upper_body'
      );

      expect(taskId).toBe('task-12345');
      expect(global.fetch).toHaveBeenCalledWith(
        'https://yce-api-01.makeupar.com/s2s/v3.0/task/cloth',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Authorization': 'Bearer test-youcam-api-key',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            src_file_url: 'https://example.com/user.jpg',
            ref_file_url: 'https://example.com/garment.jpg',
            garment_category: 'upper_body',
          }),
        })
      );
    });

    it('should throw error for invalid API key', async () => {
      const serviceWithoutKey = new YouCamService({ YOUCAM_API_KEY: '' });

      await expect(serviceWithoutKey.create_task(
        'https://example.com/user.jpg',
        'https://example.com/garment.jpg',
        'upper_body'
      )).rejects.toThrow('YouCam API key not configured');
    });

    it('should throw error for authentication failure', async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        text: () => Promise.resolve(JSON.stringify({
          error: 'Invalid API key',
          error_code: 'AUTH_FAILED'
        })),
      };

      global.fetch = vi.fn().mockResolvedValue(mockResponse);

      await expect(service.create_task(
        'https://example.com/user.jpg',
        'https://example.com/garment.jpg',
        'upper_body'
      )).rejects.toThrow('YouCam Task API error (401): Invalid API key [AUTH_FAILED]');
    });

    it('should retry on transient errors', async () => {
      const mockFailResponse = {
        ok: false,
        status: 503,
        text: () => Promise.resolve('Service unavailable'),
      };

      const mockSuccessResponse = {
        ok: true,
        status: 200,
        text: () => Promise.resolve(JSON.stringify({
          data: { task_id: 'task-12345' }
        })),
      };

      global.fetch = vi.fn()
        .mockResolvedValueOnce(mockFailResponse)
        .mockResolvedValueOnce(mockSuccessResponse);

      const taskId = await service.create_task(
        'https://example.com/user.jpg',
        'https://example.com/garment.jpg',
        'upper_body'
      );

      expect(taskId).toBe('task-12345');
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    it('should not retry on auth errors', async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        text: () => Promise.resolve(JSON.stringify({
          error: 'Invalid API key',
          error_code: 'AUTH_FAILED'
        })),
      };

      global.fetch = vi.fn().mockResolvedValue(mockResponse);

      await expect(service.create_task(
        'https://example.com/user.jpg',
        'https://example.com/garment.jpg',
        'upper_body'
      )).rejects.toThrow('YouCam Task API error (401): Invalid API key [AUTH_FAILED]');

      expect(global.fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('poll_task', () => {
    it('should poll until completed', async () => {
      const mockProcessingResponse = {
        ok: true,
        status: 200,
        text: () => Promise.resolve(JSON.stringify({
          data: {
            task_status: 'processing',
          }
        })),
      };

      const mockCompletedResponse = {
        ok: true,
        status: 200,
        text: () => Promise.resolve(JSON.stringify({
          data: {
            task_status: 'success',
            results: { url: 'https://example.com/result.jpg' }
          }
        })),
      };

      global.fetch = vi.fn()
        .mockResolvedValueOnce(mockProcessingResponse)
        .mockResolvedValueOnce(mockCompletedResponse);

      const result = await service.poll_task('task-12345');

      expect(result.status).toBe('completed');
      expect(result.output_url).toBe('https://example.com/result.jpg');
    });

    it('should return failed status on error', async () => {
      const mockFailedResponse = {
        ok: true,
        status: 200,
        text: () => Promise.resolve(JSON.stringify({
          data: {
            task_status: 'error',
            error: 'Processing failed'
          }
        })),
      };

      global.fetch = vi.fn().mockResolvedValueOnce(mockFailedResponse);

      const result = await service.poll_task('task-12345');

      expect(result.status).toBe('failed');
      expect(result.error).toBe('Processing failed');
    });

    it('should handle missing task_id', async () => {
      await expect(service.poll_task('')).rejects.toThrow('task_id is required');
    });
  });

  describe('verify_webhook_signature', () => {
    it('should verify valid signature', () => {
      const payload = '{"data":{"task_id":"task-123","task_status":"success"}}';
      const secret = 'test-secret';
      const crypto = require('crypto');
      const signature = crypto
        .createHmac('sha256', Buffer.from(secret, 'base64'))
        .update(payload)
        .digest('base64');
      const signatureHeader = `v1,${signature}`;

      const result = YouCamService.verify_webhook_signature(payload, signatureHeader, secret);

      expect(result).toBe(true);
    });

    it('should reject invalid signature', () => {
      const result = YouCamService.verify_webhook_signature(
        'payload',
        'v1,invalidsignature',
        'secret'
      );

      expect(result).toBe(false);
    });

    it('should reject malformed signature header', () => {
      const result = YouCamService.verify_webhook_signature(
        'payload',
        'invalid-header',
        'secret'
      );

      expect(result).toBe(false);
    });

    it('should handle missing signature', () => {
      const result = YouCamService.verify_webhook_signature('payload', '', 'secret');
      expect(result).toBe(false);
    });

    it('should handle missing secret', () => {
      const result = YouCamService.verify_webhook_signature('payload', 'v1,sig', '');
      expect(result).toBe(false);
    });
  });
});