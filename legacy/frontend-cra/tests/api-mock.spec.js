// @ts-check
import { test, expect } from '@playwright/test';

test.describe('Navegacion', () => {
  test('deberia navegar entre home y catalogo sin errores', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Catalogo' }).first().click();

    // La URL deberia haber cambiado a catalog
    await expect(page).toHaveURL(/\/catalog/);
  });

  test('deberia interceptar la API y renderizar products vacios', async ({ page }) => {
    // Mock de la API de productos para no depender del backend real
    await page.route('**/api/v1/products**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ products: [], total: 0 }),
      });
    });

    await page.goto('/catalog');

    // La pagina deberia cargar sin errores de network
    await expect(page.locator('#root')).not.toBeEmpty();
  });

  test('deberia tomar screenshot en fallo (ejemplo de debug)', async ({ page }) => {
    await page.goto('/login');

    // Este test pasa pero demuestra que Playwright guarda evidencia si falla
    const emailInput = page.getByPlaceholder(/email/i);
    await expect(emailInput).toBeInViewport();

    // Si necesitas forzar una falla para ver el reporte:
    // await expect(page.getByText('texto que no existe')).toBeVisible();
  });
});
