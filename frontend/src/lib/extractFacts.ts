export interface Fact {
  concept: string;
  details: string;
  confidence: number;
}

export function extractFacts(text: string): Fact[] {
  const facts: Fact[] = [];

  // Simple keyword-based extraction (can be enhanced with NLP)
  const sentences = text.split(/[.!?]+/).filter((s) => s.trim().length > 0);

  // Keywords that indicate important concepts
  const keywordPatterns = [
    /photosynthesis/i,
    /chlorophyll/i,
    /carbon dioxide|CO2/i,
    /oxygen|O2/i,
    /glucose/i,
    /solar system/i,
    /planet/i,
    /gravity/i,
    /cell/i,
    /nucleus/i,
    /mitochondria/i,
    /DNA/i,
    /water cycle/i,
    /evaporation/i,
    /condensation/i,
    /precipitation/i,
  ];

  sentences.forEach((sentence) => {
    keywordPatterns.forEach((pattern) => {
      if (pattern.test(sentence)) {
        const match = sentence.match(pattern);
        const concept = match?.[0] ?? '';
        facts.push({
          concept: concept,
          details: sentence.trim(),
          confidence: 0.8,
        });
      }
    });
  });

  // Deduplicate
  const uniqueFacts = facts.filter(
    (fact, index, self) =>
      index ===
      self.findIndex(
        (f) => f.concept.toLowerCase() === fact.concept.toLowerCase(),
      ),
  );

  return uniqueFacts.slice(0, 10); // Limit to 10 facts
}

