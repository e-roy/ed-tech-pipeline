import { getPdfjsLib } from './pdfWorker';

export async function extractTextFromPDF(file: File): Promise<string> {
  const pdfjsLib = await getPdfjsLib();
  const arrayBuffer = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;

  let fullText = '';

  for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
    const page = await pdf.getPage(pageNum);
    const textContent = await page.getTextContent();
    const pageText = textContent.items
      .map((item) => {
        // Type guard for text items
        if ('str' in item) {
          return item.str;
        }
        return '';
      })
      .join(' ');
    fullText += pageText + '\n';
  }

  return fullText;
}

