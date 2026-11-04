// @ts-check
import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test('deberia renderizar el formulario de login', async ({ page }) => {
    await page.goto('/login');

    // El titulo de la pagina
    await expect(page.getByRole('heading', { name: /iniciar sesion/i })).toBeVisible();

    // El campo de email usando su placeholder como selector
    const emailInput = page.getByPlaceholder(/email/i);
    await expect(emailInput).toBeVisible();

    // El formulario tiene un input de password (aunque el placeholder sea en ingles o vacio)
    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput).toBeVisible();
  });

  test('deberia permitir escribir email y password', async ({ page }) => {
    await page.goto('/login');

    const emailInput = page.getByPlaceholder(/email/i);
    const passwordInput = page.locator('input[type="password"]');

    await emailInput.fill('test@ejemplo.cl');
    await passwordInput.fill('supersecreto123');

    await expect(emailInput).toHaveValue('test@ejemplo.cl');
    await expect(passwordInput).toHaveValue('supersecreto123');
  });

  test('deberia tener un link para ir a registro', async ({ page }) => {
    await page.goto('/login');

    // El link real en la pagina dice "Registrate"
    const registerLink = page.getByRole('link', { name: /registrate/i }).first();
    await expect(registerLink).toHaveAttribute('href', '/register');
  });
});
