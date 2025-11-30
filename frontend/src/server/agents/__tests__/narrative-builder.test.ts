import { NarrativeBuilderAgent } from "../narrative-builder";
import type { AgentInput } from "@/types/agent";

async function testAgent() {
  const agent = new NarrativeBuilderAgent();

  const input: AgentInput = {
    data: {
      topic: "Photosynthesis",
      facts: [
        {
          concept: "photosynthesis",
          details: "Process where plants make food from sunlight",
        },
        {
          concept: "chlorophyll",
          details: "Green pigment that captures light",
        },
        {
          concept: "glucose",
          details: "Sugar produced as plant food",
        },
      ],
      target_duration: 60,
    },
  };

  const result = await agent.process(input);
  console.log("Success:", result.success);
  console.log("Cost:", `$${result.cost.toFixed(4)}`);
  console.log("Duration:", `${result.duration.toFixed(2)}s`);
  if (result.success) {
    const script = result.data.script as { segments: unknown[] };
    console.log("Script segments:", script.segments.length);
  } else {
    console.log("Error:", result.error);
  }
}

testAgent().catch(console.error);
