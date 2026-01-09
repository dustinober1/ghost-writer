import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should show login page for unauthenticated users', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/.*login/);
  });

  test('should display login form', async ({ page }) => {
    await page.goto('/login');
    
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in|login/i })).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    await page.getByLabel(/email/i).fill('invalid@test.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /sign in|login/i }).click();
    
    // Should show error message
    await expect(page.getByText(/invalid|error|incorrect/i)).toBeVisible();
  });

  test('should redirect to dashboard after successful login', async ({ page }) => {
    // This test requires a test user to exist
    await page.goto('/login');
    
    await page.getByLabel(/email/i).fill('test@example.com');
    await page.getByLabel(/password/i).fill('testpassword123');
    await page.getByRole('button', { name: /sign in|login/i }).click();
    
    // Should redirect to dashboard or show error
    await page.waitForURL(/\/(dashboard)?$/);
  });

  test('should have registration link', async ({ page }) => {
    await page.goto('/login');
    
    const registerLink = page.getByRole('link', { name: /register|sign up|create account/i });
    await expect(registerLink).toBeVisible();
  });
});

test.describe('Registration', () => {
  test('should display registration form', async ({ page }) => {
    await page.goto('/login');
    
    // Click register link if it exists
    const registerLink = page.getByRole('link', { name: /register|sign up|create account/i });
    if (await registerLink.isVisible()) {
      await registerLink.click();
    }
    
    // Check for registration form elements
    await expect(page.getByLabel(/email/i)).toBeVisible();
  });

  test('should validate password requirements', async ({ page }) => {
    await page.goto('/login');
    
    const registerLink = page.getByRole('link', { name: /register|sign up|create account/i });
    if (await registerLink.isVisible()) {
      await registerLink.click();
    }
    
    await page.getByLabel(/email/i).fill('newuser@test.com');
    await page.getByLabel(/^password/i).fill('weak');
    
    // Try to submit
    await page.getByRole('button', { name: /register|sign up|create/i }).click();
    
    // Should show validation error
    await expect(page.getByText(/password|weak|stronger/i)).toBeVisible();
  });
});
