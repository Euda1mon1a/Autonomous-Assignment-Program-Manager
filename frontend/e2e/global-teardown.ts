import { FullConfig } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Global Teardown
 *
 * Runs once after all tests:
 * - Clean up test data
 * - Remove authentication states
 * - Generate test reports
 * - Clean up temporary files
 */

async function globalTeardown(config: FullConfig) {
  console.log('\n🧹 Starting E2E Test Cleanup...\n');

  const apiURL = process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000';

  // 1. Clean up test database
  console.log('✓ Cleaning up test database...');
  try {
    const response = await fetch(`${apiURL}/api/v1/test/cleanup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      console.log('  ✓ Test data cleaned up');
    } else {
      console.warn('  ⚠ Could not clean up test data (non-critical)');
    }
  } catch (error) {
    console.warn('  ⚠ Cleanup endpoint not available (non-critical)');
  }

  // 2. Clean up authentication states
  if (process.env.CI || process.env.CLEAN_AUTH_STATE === 'true') {
    console.log('✓ Removing authentication states...');
    const authDir = path.join(__dirname, '.auth');
    if (fs.existsSync(authDir)) {
      fs.rmSync(authDir, { recursive: true, force: true });
      console.log('  ✓ Authentication states removed');
    }
  }

  // 3. Generate summary report
  console.log('✓ Generating test summary...');
  await generateTestSummary();

  // 4. Clean up old test artifacts (keep last 10 runs)
  if (process.env.CI) {
    console.log('✓ Cleaning up old test artifacts...');
    await cleanupOldArtifacts();
  }

  console.log('\n✅ E2E Test Cleanup Complete!\n');
}

/**
 * Generate test summary report
 */
async function generateTestSummary(): Promise<void> {
  const resultsFile = path.join(__dirname, 'test-results/results.json');

  if (!fs.existsSync(resultsFile)) {
    console.log('  ℹ No test results found');
    return;
  }

  try {
    const resultsData = fs.readFileSync(resultsFile, 'utf-8');
    const results = JSON.parse(resultsData);

    const summary = {
      total: results.suites?.reduce((sum: number, suite: any) => sum + suite.specs.length, 0) || 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      duration: results.stats?.duration || 0,
    };

    // Count test results
    results.suites?.forEach((suite: any) => {
      suite.specs.forEach((spec: any) => {
        spec.tests.forEach((test: any) => {
          test.results.forEach((result: any) => {
            if (result.status === 'passed') summary.passed++;
            else if (result.status === 'failed') summary.failed++;
            else if (result.status === 'skipped') summary.skipped++;
          });
        });
      });
    });

    console.log('\n📊 Test Summary:');
    console.log(`  Total Tests: ${summary.total}`);
    console.log(`  ✓ Passed: ${summary.passed}`);
    console.log(`  ✗ Failed: ${summary.failed}`);
    console.log(`  ⊘ Skipped: ${summary.skipped}`);
    console.log(`  ⏱ Duration: ${(summary.duration / 1000).toFixed(2)}s`);

    // Save summary
    const summaryFile = path.join(__dirname, 'test-results/summary.json');
    fs.writeFileSync(summaryFile, JSON.stringify(summary, null, 2));
    console.log(`\n  ✓ Summary saved to: ${summaryFile}`);
  } catch (error) {
    console.warn('  ⚠ Could not generate test summary:', error);
  }
}

/**
 * Clean up old test artifacts (keep last 10 runs)
 */
async function cleanupOldArtifacts(): Promise<void> {
  const artifactDirs = ['screenshots', 'videos', 'traces'];

  for (const dirName of artifactDirs) {
    const dirPath = path.join(__dirname, 'test-results', dirName);

    if (!fs.existsSync(dirPath)) continue;

    try {
      const files = fs.readdirSync(dirPath);

      // Sort by modification time (newest first)
      const filesWithStats = files.map((file) => {
        const filePath = path.join(dirPath, file);
        const stats = fs.statSync(filePath);
        return { file, filePath, mtime: stats.mtime };
      });

      filesWithStats.sort((a, b) => b.mtime.getTime() - a.mtime.getTime());

      // Keep only last 10 files
      const filesToDelete = filesWithStats.slice(10);

      for (const { filePath } of filesToDelete) {
        fs.rmSync(filePath, { recursive: true, force: true });
      }

      if (filesToDelete.length > 0) {
        console.log(`  ✓ Cleaned up ${filesToDelete.length} old ${dirName}`);
      }
    } catch (error) {
      console.warn(`  ⚠ Could not clean up ${dirName}:`, error);
    }
  }
}

export default globalTeardown;
