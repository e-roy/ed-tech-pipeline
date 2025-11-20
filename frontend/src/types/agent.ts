export interface AgentInput {
  sessionId: string;
  data: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface AgentOutput {
  success: boolean;
  data: Record<string, unknown>;
  cost: number; // USD
  duration: number; // seconds
  error?: string;
}
