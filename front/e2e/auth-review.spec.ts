import { test, expect } from '@playwright/test';

test('ログインページが表示される', async ({ page }) => {
  await page.goto('/login');
  await expect(page.locator('form')).toBeVisible();
});

test('ログインページに email/password フィールドがある', async ({ page }) => {
  await page.goto('/login');
  await expect(page.locator('input[type="email"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
});

test('登録ページが表示される', async ({ page }) => {
  await page.goto('/register');
  await expect(page.locator('form')).toBeVisible();
});

test('登録ページに username/email/password フィールドがある', async ({ page }) => {
  await page.goto('/register');
  await expect(page.locator('input[placeholder*="ユーザー名"], input[formcontrolname="username"]')).toBeVisible();
  await expect(page.locator('input[type="email"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
});
