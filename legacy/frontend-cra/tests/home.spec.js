// @ts-check
import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('deberia cargar el titulo y estructura basica', async ({ page }) => {
    await page.goto('/');

    // El documento deberia tener un titulo no vacio
    const title = await page.title();
    expect(title).toBeTruthy();

    // La app React deberia renderizar en el root
    const root = page.locator('#root');
    await expect(root).not.toBeEmpty();
  });

  test('deberia mostrar la seccion hero con texto de marca', async ({ page }) => {
    await page.goto('/');

    // Busca el texto de marca que aparece en el hero
    const brand = page.getByText(/FT\. ?THE LINE ONE/i).first();
    await expect(brand).toBeVisible();
  });

  test('deberia tener links de navegacion (Catalogo, Try-On IA)', async ({ page }) => {
    await page.goto('/');

    // En el navbar hay links de navegacion reales
    await expect(page.getByRole('link', { name: 'Catalogo' }).first()).toBeAttached();
    await expect(page.getByRole('link', { name: 'Try-On IA' }).first()).toBeAttached();
  });
});
