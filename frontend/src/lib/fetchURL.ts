export async function fetchURLContent(url: string): Promise<string> {
  // Ensure URL has a protocol
  let fullUrl = url;
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    fullUrl = `https://${url}`;
  }

  // Try multiple CORS proxies for better reliability
  const proxies = [
    'https://api.allorigins.win/get?url=',
    'https://corsproxy.io/?',
    'https://api.codetabs.com/v1/proxy?quest=',
  ];

  let lastError: Error | null = null;

  for (const proxyUrl of proxies) {
    try {
      const response = await fetch(
        proxyUrl + encodeURIComponent(fullUrl),
        {
          // Add timeout and better error handling
          signal: AbortSignal.timeout(10000), // 10 second timeout
        },
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Check if response has content
      const text = await response.text();
      if (!text || text.trim().length === 0) {
        throw new Error('Empty response from proxy');
      }

      // Try to parse JSON (allorigins.win format)
      let data: { contents?: string; content?: string };
      try {
        data = JSON.parse(text) as { contents?: string; content?: string };
      } catch {
        // Some proxies return the content directly
        if (text.trim().length > 100) {
          // Assume it's direct content if it's substantial
          const extractedText = text
            .replace(/<[^>]*>/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
          if (extractedText.length > 0) {
            return extractedText;
          }
        }
        throw new Error(`Invalid JSON response: ${text.substring(0, 100)}`);
      }

      // Handle different proxy response formats
      const content = data.contents ?? data.content;
      if (!content) {
        throw new Error('No content received from URL');
      }

      // Strip HTML tags (basic)
      const extractedText = content
        .replace(/<[^>]*>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

      if (!extractedText || extractedText.length === 0) {
        throw new Error('No text content extracted from URL');
      }

      return extractedText;
    } catch (error) {
      // Store error and try next proxy
      if (error instanceof Error) {
        lastError = error;
        // If it's a timeout or network error, try next proxy
        if (
          error.name === 'AbortError' ||
          error.message.includes('Failed to fetch') ||
          error.message.includes('QUIC')
        ) {
          continue;
        }
        // If it's a parsing error, the proxy format might be wrong, try next
        if (error.message.includes('JSON') || error.message.includes('Invalid')) {
          continue;
        }
      }
      // For other errors, try next proxy
      continue;
    }
  }

  // All proxies failed
  console.error('All URL fetch proxies failed. Last error:', lastError);
  throw new Error(
    `Failed to fetch URL content after trying multiple proxies: ${lastError?.message ?? 'Unknown error'}`,
  );
}

