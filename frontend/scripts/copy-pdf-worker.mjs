import { copyFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');

const source = join(rootDir, 'node_modules', 'pdfjs-dist', 'build', 'pdf.worker.min.mjs');
const dest = join(rootDir, 'public', 'pdf.worker.min.mjs');

try {
  copyFileSync(source, dest);
  console.log('✓ PDF.js worker copied to public folder');
} catch (error) {
  console.error('✗ Failed to copy PDF.js worker:', error.message);
  process.exit(1);
}

