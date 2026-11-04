import { test, expect } from '@playwright/test';

test.describe('Critical User Flows', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load home page', async ({ page }) => {
    await expect(page).toHaveTitle(/FT\. THE LINE ONE/);
    await expect(page.locator('h1')).toContainText('Prueba cualquier prenda con IA');
  });

  test('should navigate to catalog', async ({ page }) => {
    await page.click('a[href="/catalog"]');
    await expect(page).toHaveURL(/.*catalog/);
    await expect(page.locator('h1')).toContainText('Catálogo');
  });

  test('should navigate to virtual try-on', async ({ page }) => {
    await page.click('a[href="/virtual-try-on"]');
    await expect(page).toHaveURL(/.*virtual-try-on/);
    await expect(page.locator('h1')).toContainText('Virtual Try-On');
  });

  test('should show login page', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('h1')).toContainText('Iniciar Sesión');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should show register page', async ({ page }) => {
    await page.goto('/register');
    await expect(page.locator('h1')).toContainText('Crea tu cuenta');
  });

  test.describe('Virtual Try-On Flow', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/virtual-try-on');
      // Mock authentication
      await page.evaluate(() => {
        localStorage.setItem('token', 'test-token');
        localStorage.setItem('refresh_token', 'test-refresh-token');
      });
      await page.reload();
    });

    test('should show product selector', async ({ page }) => {
      await expect(page.locator('select')).toBeVisible();
    });

    test('should allow image upload', async ({ page }) => {
      const fileInput = page.locator('input[type="file"]');
      await expect(fileInput).toBeVisible();

      // Create a test image file
      const testImage = Buffer.from('fake-image-data');
      await page.setInputFiles('input[type="file"]', {
        name: 'test.jpg',
        mimeType: 'image/jpeg',
        buffer: testImage,
      });
    });

    test('should show usage limit for free users', async ({ page }) => {
      await expect(page.locator('text=/Te quedan.*intentos/')).toBeVisible();
    });
  });

  test.describe('Chatbot Flow', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('/chat');
      await page.evaluate(() => {
        localStorage.setItem('token', 'test-token');
        localStorage.setItem('refresh_token', 'test-refresh-token');
      });
      await page.reload();
    });

    test('should show chat interface', async ({ page }) => {
      await expect(page.locator('h1')).toContainText('Asesor IA');
      await expect(page.locator('input[placeholder*="Escribe tu pregunta"]')).toBeVisible();
    });

    test('should send and receive message', async ({ page }) => {
      test.skip(true, 'Requires backend');
    });
  });

  test.describe('Authentication', () => {
    test('should register new user', async ({ page }) => {
      await page.goto('/register');
      await page.fill('input[name="name"]', 'Test User');
      await page.fill('input[name="email"]', `test${Date.now()}@example.com`);
      await page.fill('input[name="password"]', 'Password123!');
      await page.fill('input[name="confirm_password"]', 'Password123!');
      await page.check('input[name="terms"]');

      test.skip();
    });

    test('should login existing user', async ({ page }) => {
      await page.goto('/login');
      await page.fill('input[name="email"]', 'test@example.com');
      await page.fill('input[name="password"]', 'Password123!');
      await page.click('button[type="submit"]');

      test.skip();
    });

    test('should show error for invalid credentials', async ({ page }) => {
      await page.goto('/login');
      await page.fill('input[name="email"]', 'wrong@example.com');
      await page.fill('input[name="password"]', 'wrongpassword');
      await page.click('button[type="submit"]');
      await expect(page.locator('text=/credenciales incorrectas/i')).toBeVisible();
    });
  });

  test.describe('Payment Flow', () => {
    test('should redirect to Transbank for premium upgrade', async ({ page }) => {
      await page.goto('/profile');
      await page.click('button:has-text("Actualizar a Premium")');
      await expect(page).toHaveURL(/webpay3gint\.transbank\.cl/, { timeout: 15000 });
    });
  });

  test.describe('Mobile Responsiveness', () => {
    test.use({ ...devices['iPhone 12'] });

    test('should work on mobile', async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('h1')).toBeVisible();
    });

    test('should navigate catalog on mobile', async ({ page }) => {
      await page.goto('/catalog');
      await expect(page.locator('h1')).toContainText('Catálogo');
    });
  });
});