import { test, expect } from '@playwright/test';

// Helper to login before tests
async function loginAsTestUser(page: any) {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('test@example.com');
  await page.getByLabel(/password/i).fill('testpassword123');
  await page.getByRole('button', { name: /sign in|login/i }).click();
  await page.waitForURL(/\/(dashboard)?$/);
}

test.describe('Text Analysis', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('should navigate to analyze page', async ({ page }) => {
    await page.goto('/');
    
    // Click on analyze link in navigation
    const analyzeLink = page.getByRole('link', { name: /analyze|detect/i });
    if (await analyzeLink.isVisible()) {
      await analyzeLink.click();
      await expect(page).toHaveURL(/.*analyze/);
    }
  });

  test('should have text input area', async ({ page }) => {
    await page.goto('/analyze');
    
    const textarea = page.getByRole('textbox');
    await expect(textarea).toBeVisible();
  });

  test('should analyze text and show results', async ({ page }) => {
    await page.goto('/analyze');
    
    const testText = `
      Artificial intelligence is transforming the world. 
      Machine learning enables computers to learn from data.
      This technology has many applications in various fields.
    `;
    
    const textarea = page.getByRole('textbox');
    await textarea.fill(testText);
    
    // Click analyze button
    const analyzeButton = page.getByRole('button', { name: /analyze|detect|check/i });
    await analyzeButton.click();
    
    // Wait for results
    await expect(page.getByText(/probability|score|result/i)).toBeVisible({ timeout: 30000 });
  });

  test('should show heat map visualization', async ({ page }) => {
    await page.goto('/analyze');
    
    const testText = 'This is a sample text for analysis. It has multiple sentences.';
    
    await page.getByRole('textbox').fill(testText);
    await page.getByRole('button', { name: /analyze|detect|check/i }).click();
    
    // Wait for heat map
    await page.waitForSelector('[class*="heat"]', { timeout: 30000 });
  });
});

test.describe('Profile Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('should navigate to profile page', async ({ page }) => {
    await page.goto('/');
    
    const profileLink = page.getByRole('link', { name: /profile|fingerprint/i });
    if (await profileLink.isVisible()) {
      await profileLink.click();
      await expect(page).toHaveURL(/.*profile/);
    }
  });

  test('should allow uploading writing samples', async ({ page }) => {
    await page.goto('/profile');
    
    // Check for upload functionality
    const uploadArea = page.getByText(/upload|add sample|drop/i);
    await expect(uploadArea).toBeVisible();
  });
});

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsTestUser(page);
  });

  test('should display dashboard stats', async ({ page }) => {
    await page.goto('/');
    
    // Check for dashboard elements
    await expect(page.getByText(/analysis|analyses|recent/i)).toBeVisible();
  });

  test('should show recent activity', async ({ page }) => {
    await page.goto('/');
    
    // Check for history/activity section
    const activitySection = page.getByText(/recent|history|activity/i);
    await expect(activitySection).toBeVisible();
  });
});
