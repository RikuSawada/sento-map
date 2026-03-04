import { test, expect } from '@playwright/test';

test('地図ページが表示される', async ({ page }) => {
  await page.goto('/map');
  await expect(page).toHaveURL(/map/);
  // Google Maps API キーなしでもページ自体は表示される
  await expect(page.locator('app-map')).toBeVisible();
});

test('銭湯マップのラッパー要素が存在する', async ({ page }) => {
  await page.goto('/map');
  await expect(page.locator('.map-wrapper')).toBeVisible();
});
