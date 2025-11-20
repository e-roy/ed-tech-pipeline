import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring } from "remotion";
import React from "react";

// Common molecule types
export type MoleculeType = "CO2" | "H2O" | "O2" | "Glucose" | "custom";

// Diagram types available
export type DiagramType =
  | "chemical-reaction"
  | "process-flow"
  | "molecular"
  | "comparison"
  | "timeline"
  | "cycle";

// Molecule component for scientific diagrams
export const Molecule: React.FC<{
  type: MoleculeType;
  x: number;
  y: number;
  scale?: number;
  animationDelay?: number;
  customLabel?: string;
  customColor?: string;
}> = ({ type, x, y, scale = 1, animationDelay = 0, customLabel, customColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: Math.max(0, frame - animationDelay),
    fps,
    config: { damping: 12, stiffness: 100, mass: 0.5 },
  });

  // Gentle floating animation
  const float = Math.sin((frame - animationDelay) / 30) * 3;

  const getMoleculeConfig = () => {
    switch (type) {
      case "CO2":
        return { color: "#666666", label: "CO₂", size: 40 };
      case "H2O":
        return { color: "#4FC3F7", label: "H₂O", size: 35 };
      case "O2":
        return { color: "#EF5350", label: "O₂", size: 35 };
      case "Glucose":
        return { color: "#FFB300", label: "C₆H₁₂O₆", size: 50 };
      case "custom":
        return { color: customColor || "#9C27B0", label: customLabel || "?", size: 40 };
      default:
        return { color: "#9E9E9E", label: "?", size: 40 };
    }
  };

  const config = getMoleculeConfig();

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        transform: `translate(-50%, -50%) scale(${entrance * scale}) translateY(${float}px)`,
        opacity: entrance,
      }}
    >
      {/* Molecule body */}
      <div
        style={{
          width: config.size,
          height: config.size,
          borderRadius: "50%",
          background: `radial-gradient(circle at 30% 30%, ${config.color}88, ${config.color})`,
          boxShadow: `0 4px 12px ${config.color}44, 0 0 20px ${config.color}22`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <span
          style={{
            color: "white",
            fontSize: config.size * 0.35,
            fontWeight: "bold",
            fontFamily: "system-ui, -apple-system, sans-serif",
            textShadow: "0 1px 2px rgba(0,0,0,0.3)",
          }}
        >
          {config.label}
        </span>
      </div>
    </div>
  );
};

// Arrow component for process flows
export const FlowArrow: React.FC<{
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  color?: string;
  animationDelay?: number;
  label?: string;
}> = ({ startX, startY, endX, endY, color = "#4CAF50", animationDelay = 0, label }) => {
  const frame = useCurrentFrame();

  const progress = interpolate(
    frame - animationDelay,
    [0, 45],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const angle = Math.atan2(endY - startY, endX - startX) * (180 / Math.PI);
  const length = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));

  return (
    <div
      style={{
        position: "absolute",
        left: `${startX}%`,
        top: `${startY}%`,
        width: `${length}%`,
        height: "4px",
        background: color,
        transform: `rotate(${angle}deg) scaleX(${progress})`,
        transformOrigin: "left center",
        opacity: progress,
      }}
    >
      {/* Arrowhead */}
      <div
        style={{
          position: "absolute",
          right: "-8px",
          top: "50%",
          transform: "translateY(-50%)",
          width: 0,
          height: 0,
          borderLeft: `12px solid ${color}`,
          borderTop: "6px solid transparent",
          borderBottom: "6px solid transparent",
        }}
      />
      {/* Label */}
      {label && (
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "-20px",
            transform: `translateX(-50%) rotate(-${angle}deg)`,
            color: color,
            fontSize: "12px",
            fontWeight: "bold",
            whiteSpace: "nowrap",
          }}
        >
          {label}
        </div>
      )}
    </div>
  );
};

// Box component for diagrams
export const DiagramBox: React.FC<{
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  label: string;
  animationDelay?: number;
}> = ({ x, y, width, height, color = "#2196F3", label, animationDelay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame: Math.max(0, frame - animationDelay),
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        width: `${width}%`,
        height: `${height}%`,
        background: `${color}22`,
        border: `2px solid ${color}`,
        borderRadius: "8px",
        transform: `scale(${entrance})`,
        opacity: entrance,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <span
        style={{
          color: color,
          fontSize: "18px",
          fontWeight: "bold",
          textAlign: "center",
          padding: "8px",
        }}
      >
        {label}
      </span>
    </div>
  );
};

// Chemical reaction diagram
export const ChemicalReactionDiagram: React.FC<{
  reactants: Array<{ type: MoleculeType; count: number }>;
  products: Array<{ type: MoleculeType; count: number }>;
  title?: string;
}> = ({ reactants, products, title }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleEntrance = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 80 },
  });

  return (
    <AbsoluteFill style={{ background: "linear-gradient(135deg, #1a237e 0%, #283593 100%)" }}>
      {/* Title */}
      {title && (
        <div
          style={{
            position: "absolute",
            top: "8%",
            left: "50%",
            transform: `translateX(-50%) scale(${titleEntrance})`,
            color: "white",
            fontSize: "36px",
            fontWeight: "bold",
            textAlign: "center",
            textShadow: "0 2px 8px rgba(0,0,0,0.3)",
          }}
        >
          {title}
        </div>
      )}

      {/* Reactants */}
      {reactants.map((reactant, i) => {
        const totalReactants = reactants.reduce((sum, r) => sum + r.count, 0);
        let moleculeIndex = 0;
        for (let j = 0; j < i; j++) {
          moleculeIndex += reactants[j].count;
        }

        return Array.from({ length: reactant.count }).map((_, k) => (
          <Molecule
            key={`reactant-${i}-${k}`}
            type={reactant.type}
            x={15 + ((moleculeIndex + k) / totalReactants) * 20}
            y={50 + (k % 2) * 10 - 5}
            animationDelay={(moleculeIndex + k) * 8}
          />
        ));
      })}

      {/* Arrow */}
      <FlowArrow
        startX={38}
        startY={50}
        endX={58}
        endY={50}
        color="#FFD700"
        animationDelay={40}
        label="→"
      />

      {/* Products */}
      {products.map((product, i) => {
        const totalProducts = products.reduce((sum, p) => sum + p.count, 0);
        let moleculeIndex = 0;
        for (let j = 0; j < i; j++) {
          moleculeIndex += products[j].count;
        }

        return Array.from({ length: product.count }).map((_, k) => (
          <Molecule
            key={`product-${i}-${k}`}
            type={product.type}
            x={65 + ((moleculeIndex + k) / totalProducts) * 20}
            y={50 + (k % 2) * 10 - 5}
            animationDelay={60 + (moleculeIndex + k) * 8}
          />
        ));
      })}
    </AbsoluteFill>
  );
};

// Process flow diagram
export const ProcessFlowDiagram: React.FC<{
  steps: Array<{ label: string; color?: string }>;
  title?: string;
}> = ({ steps, title }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleEntrance = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 80 },
  });

  const stepWidth = 80 / steps.length;
  const stepHeight = 15;

  return (
    <AbsoluteFill style={{ background: "linear-gradient(135deg, #0d47a1 0%, #1565c0 100%)" }}>
      {/* Title */}
      {title && (
        <div
          style={{
            position: "absolute",
            top: "8%",
            left: "50%",
            transform: `translateX(-50%) scale(${titleEntrance})`,
            color: "white",
            fontSize: "36px",
            fontWeight: "bold",
            textAlign: "center",
          }}
        >
          {title}
        </div>
      )}

      {/* Steps */}
      {steps.map((step, i) => (
        <React.Fragment key={i}>
          <DiagramBox
            x={10 + i * stepWidth}
            y={42.5}
            width={stepWidth - 5}
            height={stepHeight}
            color={step.color || "#4CAF50"}
            label={step.label}
            animationDelay={i * 20}
          />
          {i < steps.length - 1 && (
            <FlowArrow
              startX={10 + i * stepWidth + stepWidth - 5}
              startY={50}
              endX={10 + (i + 1) * stepWidth}
              endY={50}
              animationDelay={i * 20 + 15}
            />
          )}
        </React.Fragment>
      ))}
    </AbsoluteFill>
  );
};

// Comparison diagram (side by side)
export const ComparisonDiagram: React.FC<{
  leftTitle: string;
  rightTitle: string;
  leftItems: string[];
  rightItems: string[];
  leftColor?: string;
  rightColor?: string;
}> = ({ leftTitle, rightTitle, leftItems, rightItems, leftColor = "#4CAF50", rightColor = "#F44336" }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleEntrance = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 80 },
  });

  return (
    <AbsoluteFill style={{ background: "linear-gradient(135deg, #263238 0%, #37474f 100%)" }}>
      {/* Left side */}
      <div
        style={{
          position: "absolute",
          left: "5%",
          top: "20%",
          width: "40%",
          transform: `scale(${titleEntrance})`,
        }}
      >
        <h2 style={{ color: leftColor, fontSize: "28px", marginBottom: "20px", textAlign: "center" }}>
          {leftTitle}
        </h2>
        {leftItems.map((item, i) => (
          <div
            key={i}
            style={{
              color: "white",
              fontSize: "18px",
              padding: "8px 16px",
              marginBottom: "8px",
              background: `${leftColor}22`,
              borderLeft: `3px solid ${leftColor}`,
              opacity: interpolate(frame - i * 10, [0, 20], [0, 1], { extrapolateRight: "clamp" }),
            }}
          >
            {item}
          </div>
        ))}
      </div>

      {/* Divider */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "15%",
          bottom: "15%",
          width: "2px",
          background: "rgba(255,255,255,0.3)",
          transform: `translateX(-50%) scaleY(${titleEntrance})`,
        }}
      />

      {/* Right side */}
      <div
        style={{
          position: "absolute",
          right: "5%",
          top: "20%",
          width: "40%",
          transform: `scale(${titleEntrance})`,
        }}
      >
        <h2 style={{ color: rightColor, fontSize: "28px", marginBottom: "20px", textAlign: "center" }}>
          {rightTitle}
        </h2>
        {rightItems.map((item, i) => (
          <div
            key={i}
            style={{
              color: "white",
              fontSize: "18px",
              padding: "8px 16px",
              marginBottom: "8px",
              background: `${rightColor}22`,
              borderLeft: `3px solid ${rightColor}`,
              opacity: interpolate(frame - i * 10, [0, 20], [0, 1], { extrapolateRight: "clamp" }),
            }}
          >
            {item}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

// Timeline diagram
export const TimelineDiagram: React.FC<{
  events: Array<{ year: string; title: string; description?: string }>;
  title?: string;
}> = ({ events, title }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ background: "linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)" }}>
      {/* Title */}
      {title && (
        <div
          style={{
            position: "absolute",
            top: "8%",
            left: "50%",
            transform: "translateX(-50%)",
            color: "white",
            fontSize: "36px",
            fontWeight: "bold",
          }}
        >
          {title}
        </div>
      )}

      {/* Timeline line */}
      <div
        style={{
          position: "absolute",
          left: "10%",
          right: "10%",
          top: "50%",
          height: "4px",
          background: "rgba(255,255,255,0.5)",
          transform: `scaleX(${interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" })})`,
          transformOrigin: "left",
        }}
      />

      {/* Events */}
      {events.map((event, i) => {
        const eventX = 15 + (i / (events.length - 1)) * 70;
        const isTop = i % 2 === 0;

        const entrance = spring({
          frame: Math.max(0, frame - 30 - i * 15),
          fps,
          config: { damping: 12, stiffness: 100 },
        });

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${eventX}%`,
              top: isTop ? "25%" : "55%",
              transform: `translateX(-50%) scale(${entrance})`,
              opacity: entrance,
              textAlign: "center",
            }}
          >
            {/* Connector */}
            <div
              style={{
                position: "absolute",
                left: "50%",
                [isTop ? "bottom" : "top"]: "-20px",
                width: "2px",
                height: "20px",
                background: "#FFD700",
                transform: "translateX(-50%)",
              }}
            />
            {/* Dot */}
            <div
              style={{
                position: "absolute",
                left: "50%",
                [isTop ? "bottom" : "top"]: "-28px",
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                background: "#FFD700",
                transform: "translateX(-50%)",
              }}
            />
            {/* Content */}
            <div style={{ color: "#FFD700", fontSize: "14px", fontWeight: "bold" }}>
              {event.year}
            </div>
            <div style={{ color: "white", fontSize: "16px", fontWeight: "bold", marginTop: "4px" }}>
              {event.title}
            </div>
            {event.description && (
              <div style={{ color: "rgba(255,255,255,0.7)", fontSize: "12px", marginTop: "4px", maxWidth: "120px" }}>
                {event.description}
              </div>
            )}
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

// Main diagram renderer that selects the appropriate diagram type
export interface DiagramConfig {
  type: DiagramType;
  title?: string;
  // Type-specific data
  chemicalReaction?: {
    reactants: Array<{ type: MoleculeType; count: number }>;
    products: Array<{ type: MoleculeType; count: number }>;
  };
  processFlow?: {
    steps: Array<{ label: string; color?: string }>;
  };
  comparison?: {
    leftTitle: string;
    rightTitle: string;
    leftItems: string[];
    rightItems: string[];
    leftColor?: string;
    rightColor?: string;
  };
  timeline?: {
    events: Array<{ year: string; title: string; description?: string }>;
  };
}

export const DiagramRenderer: React.FC<{ config: DiagramConfig }> = ({ config }) => {
  switch (config.type) {
    case "chemical-reaction":
      if (config.chemicalReaction) {
        return (
          <ChemicalReactionDiagram
            reactants={config.chemicalReaction.reactants}
            products={config.chemicalReaction.products}
            title={config.title}
          />
        );
      }
      break;

    case "process-flow":
      if (config.processFlow) {
        return (
          <ProcessFlowDiagram
            steps={config.processFlow.steps}
            title={config.title}
          />
        );
      }
      break;

    case "comparison":
      if (config.comparison) {
        return (
          <ComparisonDiagram
            leftTitle={config.comparison.leftTitle}
            rightTitle={config.comparison.rightTitle}
            leftItems={config.comparison.leftItems}
            rightItems={config.comparison.rightItems}
            leftColor={config.comparison.leftColor}
            rightColor={config.comparison.rightColor}
          />
        );
      }
      break;

    case "timeline":
      if (config.timeline) {
        return (
          <TimelineDiagram
            events={config.timeline.events}
            title={config.title}
          />
        );
      }
      break;
  }

  // Fallback
  return (
    <AbsoluteFill style={{ background: "#333", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <span style={{ color: "white", fontSize: "24px" }}>
        Diagram type not configured: {config.type}
      </span>
    </AbsoluteFill>
  );
};
