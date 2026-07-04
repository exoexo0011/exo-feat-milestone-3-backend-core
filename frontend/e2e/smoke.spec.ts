import { expect, test } from '@playwright/test';

// Full-stack smoke test: renderer -> Vite proxy -> FastAPI (echo provider).
test.describe('EXO desktop app', () => {
  test('loads the shell', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('button', { name: /new chat/i })).toBeVisible();
    await expect(page.getByLabel('Message', { exact: true })).toBeVisible();
  });

  test('sends a message and renders the streamed reply', async ({ page }) => {
    await page.goto('/');

    const input = page.getByLabel('Message', { exact: true });
    await input.fill('hello from e2e');
    await input.press('Enter');

    // The echo provider streams the user's text back, so it appears in the log.
    const log = page.getByRole('log', { name: 'Messages' });
    await expect(log.getByText('hello from e2e').first()).toBeVisible();
    // An assistant reply rendered (assistant bubbles expose a copy button).
    await expect(page.getByRole('button', { name: /copy message/i }).first()).toBeVisible({
      timeout: 15_000,
    });
  });

  test('opens settings and switches theme', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open settings' }).click();

    const dialog = page.getByRole('dialog', { name: 'Settings' });
    await expect(dialog).toBeVisible();

    await dialog.getByRole('radio', { name: 'Light' }).click();
    await expect(page.locator('html')).not.toHaveClass(/dark/);
  });
});
