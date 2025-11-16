// Dynamic import for client-side only
export async function getPdfjsLib() {
  if (typeof window === 'undefined') {
    throw new Error('PDF.js can only be used in the browser');
  }
  
  const pdfjsLib = await import('pdfjs-dist');
  
  // Use the worker from the public folder (copied during build)
  // This is more reliable than CDN and works with Next.js
  pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';
  
  return pdfjsLib;
}

