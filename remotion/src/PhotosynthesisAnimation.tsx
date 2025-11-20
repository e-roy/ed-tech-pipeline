import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
} from "remotion";

// ============================================================================
// ANIMATED COMPONENTS
// ============================================================================

// Animated Sun with rays
const AnimatedSun: React.FC<{
  x: number;
  y: number;
  size: number;
  intensity?: number;
}> = ({ x, y, size, intensity = 1 }) => {
  const frame = useCurrentFrame();

  // Pulsing glow
  const glowScale = 1 + Math.sin(frame / 20) * 0.1;
  const rayRotation = frame * 0.5;

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        transform: "translate(-50%, -50%)",
      }}
    >
      {/* Outer glow */}
      <div
        style={{
          position: "absolute",
          width: size * 2,
          height: size * 2,
          borderRadius: "50%",
          background: `radial-gradient(circle, rgba(255, 230, 100, ${0.3 * intensity}) 0%, transparent 70%)`,
          transform: `translate(-50%, -50%) scale(${glowScale})`,
          left: "50%",
          top: "50%",
        }}
      />
      {/* Sun body */}
      <div
        style={{
          width: size,
          height: size,
          borderRadius: "50%",
          background: "radial-gradient(circle, #FFE066 0%, #FFB300 100%)",
          boxShadow: `0 0 ${size / 2}px rgba(255, 180, 0, 0.8)`,
        }}
      />
      {/* Rays */}
      {[...Array(8)].map((_, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            width: 4,
            height: size * 0.8,
            background: "linear-gradient(to top, #FFE066, transparent)",
            transformOrigin: "bottom center",
            transform: `translateX(-50%) rotate(${rayRotation + i * 45}deg) translateY(-${size * 0.7}px)`,
            opacity: 0.7,
          }}
        />
      ))}
    </div>
  );
};

// Animated molecule (CO2, H2O, O2)
const Molecule: React.FC<{
  type: "co2" | "h2o" | "o2" | "glucose";
  x: number;
  y: number;
  scale?: number;
  delay?: number;
}> = ({ type, x, y, scale = 1, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const localFrame = Math.max(0, frame - delay);

  // Floating motion
  const floatY = Math.sin(localFrame / 30) * 5;
  const floatX = Math.cos(localFrame / 40) * 3;

  // Entrance animation
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 12, stiffness: 100, mass: 0.5 },
  });

  const getAtoms = () => {
    switch (type) {
      case "co2":
        return (
          <>
            <circle cx="30" cy="25" r="12" fill="#333" />
            <circle cx="50" cy="25" r="8" fill="#ff4444" />
            <circle cx="10" cy="25" r="8" fill="#ff4444" />
            <text x="30" y="29" textAnchor="middle" fontSize="8" fill="white">C</text>
            <text x="50" y="29" textAnchor="middle" fontSize="6" fill="white">O</text>
            <text x="10" y="29" textAnchor="middle" fontSize="6" fill="white">O</text>
          </>
        );
      case "h2o":
        return (
          <>
            <circle cx="30" cy="20" r="10" fill="#4444ff" />
            <circle cx="18" cy="35" r="6" fill="#ffffff" stroke="#ccc" />
            <circle cx="42" cy="35" r="6" fill="#ffffff" stroke="#ccc" />
            <text x="30" y="24" textAnchor="middle" fontSize="7" fill="white">O</text>
            <text x="18" y="38" textAnchor="middle" fontSize="5" fill="#333">H</text>
            <text x="42" y="38" textAnchor="middle" fontSize="5" fill="#333">H</text>
          </>
        );
      case "o2":
        return (
          <>
            <circle cx="20" cy="25" r="10" fill="#ff4444" />
            <circle cx="40" cy="25" r="10" fill="#ff4444" />
            <text x="20" y="29" textAnchor="middle" fontSize="7" fill="white">O</text>
            <text x="40" y="29" textAnchor="middle" fontSize="7" fill="white">O</text>
          </>
        );
      case "glucose":
        return (
          <>
            {/* Simplified hexagonal glucose */}
            <polygon
              points="30,10 45,20 45,35 30,45 15,35 15,20"
              fill="none"
              stroke="#22aa22"
              strokeWidth="2"
            />
            <circle cx="30" cy="10" r="4" fill="#333" />
            <circle cx="45" cy="20" r="4" fill="#333" />
            <circle cx="45" cy="35" r="4" fill="#ff4444" />
            <circle cx="30" cy="45" r="4" fill="#333" />
            <circle cx="15" cy="35" r="4" fill="#ff4444" />
            <circle cx="15" cy="20" r="4" fill="#333" />
          </>
        );
    }
  };

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        top: `${y}%`,
        transform: `translate(-50%, -50%) translate(${floatX}px, ${floatY}px) scale(${scale * entrance})`,
      }}
    >
      <svg width="60" height="50" viewBox="0 0 60 50">
        {getAtoms()}
      </svg>
    </div>
  );
};

// Animated plant/leaf
const AnimatedPlant: React.FC<{
  x: number;
  y: number;
  growth: number; // 0-1
  scale?: number;
}> = ({ x, y, growth, scale = 1 }) => {
  const frame = useCurrentFrame();

  // Gentle swaying
  const sway = Math.sin(frame / 40) * 3;

  const stemHeight = 100 * growth;
  const leafSize = 40 * growth;

  return (
    <div
      style={{
        position: "absolute",
        left: `${x}%`,
        bottom: `${y}%`,
        transform: `translateX(-50%) rotate(${sway}deg) scale(${scale})`,
        transformOrigin: "bottom center",
      }}
    >
      {/* Stem */}
      <div
        style={{
          width: 8,
          height: stemHeight,
          background: "linear-gradient(to top, #2d5a27, #4CAF50)",
          borderRadius: 4,
          position: "absolute",
          bottom: 0,
          left: "50%",
          transform: "translateX(-50%)",
        }}
      />
      {/* Leaves */}
      {growth > 0.3 && (
        <>
          <div
            style={{
              position: "absolute",
              bottom: stemHeight * 0.6,
              left: "50%",
              width: leafSize,
              height: leafSize * 0.6,
              background: "radial-gradient(ellipse, #66BB6A, #2E7D32)",
              borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
              transform: `translateX(-100%) rotate(-30deg)`,
              transformOrigin: "right center",
            }}
          />
          <div
            style={{
              position: "absolute",
              bottom: stemHeight * 0.6,
              left: "50%",
              width: leafSize,
              height: leafSize * 0.6,
              background: "radial-gradient(ellipse, #66BB6A, #2E7D32)",
              borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
              transform: `rotate(30deg)`,
              transformOrigin: "left center",
            }}
          />
        </>
      )}
      {growth > 0.7 && (
        <div
          style={{
            position: "absolute",
            bottom: stemHeight * 0.9,
            left: "50%",
            width: leafSize * 1.2,
            height: leafSize * 0.7,
            background: "radial-gradient(ellipse, #81C784, #388E3C)",
            borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
            transform: `translateX(-50%)`,
          }}
        />
      )}
    </div>
  );
};

// Arrow component for showing flow
const FlowArrow: React.FC<{
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  progress: number;
  color?: string;
}> = ({ x1, y1, x2, y2, progress, color = "#FFC107" }) => {
  const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
  const angle = Math.atan2(y2 - y1, x2 - x1) * (180 / Math.PI);

  return (
    <div
      style={{
        position: "absolute",
        left: `${x1}%`,
        top: `${y1}%`,
        width: `${length}%`,
        height: 4,
        background: `linear-gradient(to right, ${color}, ${color} ${progress * 100}%, transparent ${progress * 100}%)`,
        transform: `rotate(${angle}deg)`,
        transformOrigin: "left center",
      }}
    >
      {progress > 0.9 && (
        <div
          style={{
            position: "absolute",
            right: -8,
            top: -6,
            width: 0,
            height: 0,
            borderLeft: `12px solid ${color}`,
            borderTop: "8px solid transparent",
            borderBottom: "8px solid transparent",
          }}
        />
      )}
    </div>
  );
};

// Text overlay with animation
const AnimatedText: React.FC<{
  text: string;
  position: "top" | "center" | "bottom";
  color?: string;
  fontSize?: number;
  startFrame: number;
  endFrame: number;
}> = ({ text, position, color = "#ffffff", fontSize = 48, startFrame, endFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (frame < startFrame || frame > endFrame) return null;

  const localFrame = frame - startFrame;
  const duration = endFrame - startFrame;

  // Entrance
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 12, stiffness: 100, mass: 0.5 },
  });

  // Exit
  const exit = localFrame > duration - 30
    ? interpolate(localFrame, [duration - 30, duration], [1, 0], { extrapolateLeft: "clamp" })
    : 1;

  const positionStyles: React.CSSProperties = {
    top: position === "top" ? "12%" : position === "center" ? "50%" : undefined,
    bottom: position === "bottom" ? "15%" : undefined,
    left: "50%",
    transform: `translateX(-50%) ${position === "center" ? "translateY(-50%)" : ""} scale(${entrance})`,
  };

  return (
    <div
      style={{
        position: "absolute",
        ...positionStyles,
        fontSize,
        fontWeight: "bold",
        color,
        textShadow: "2px 2px 8px rgba(0,0,0,0.8), 0 0 20px rgba(0,0,0,0.5)",
        fontFamily: "system-ui, -apple-system, sans-serif",
        opacity: exit,
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};

// ============================================================================
// SCENE COMPOSITIONS
// ============================================================================

// Scene 1: Hook - Introduction with sun and leaf
const HookScene: React.FC<{ durationFrames: number }> = ({ durationFrames }) => {
  const frame = useCurrentFrame();

  const sunY = interpolate(frame, [0, durationFrames], [20, 25], { extrapolateRight: "clamp" });
  const plantGrowth = interpolate(frame, [60, durationFrames - 60], [0.2, 0.8], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: "linear-gradient(to bottom, #87CEEB 0%, #E0F7FA 100%)" }}>
      <AnimatedSun x={75} y={sunY} size={120} intensity={1.2} />

      {/* Ground */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: "25%",
          background: "linear-gradient(to bottom, #8B4513, #654321)",
        }}
      />

      <AnimatedPlant x={50} y={25} growth={plantGrowth} scale={2} />

      <AnimatedText
        text="PHOTOSYNTHESIS"
        position="top"
        color="#2d5a27"
        fontSize={72}
        startFrame={30}
        endFrame={durationFrames - 30}
      />

      <AnimatedText
        text="How plants make food from sunlight"
        position="bottom"
        color="#ffffff"
        fontSize={36}
        startFrame={120}
        endFrame={durationFrames - 30}
      />
    </AbsoluteFill>
  );
};

// Scene 2: Concept - Chloroplasts and chlorophyll
const ConceptScene: React.FC<{ durationFrames: number }> = ({ durationFrames }) => {
  const frame = useCurrentFrame();

  // Cell membrane animation
  const pulseScale = 1 + Math.sin(frame / 30) * 0.02;

  // Chloroplast positions
  const chloroplasts = [
    { x: 35, y: 40 },
    { x: 55, y: 35 },
    { x: 45, y: 55 },
    { x: 60, y: 50 },
    { x: 40, y: 60 },
  ];

  return (
    <AbsoluteFill style={{ background: "linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)" }}>
      {/* Cell membrane */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: 500,
          height: 400,
          border: "8px solid #81C784",
          borderRadius: "40% 60% 60% 40% / 60% 40% 60% 40%",
          transform: `translate(-50%, -50%) scale(${pulseScale})`,
          background: "rgba(200, 230, 201, 0.5)",
        }}
      />

      {/* Chloroplasts */}
      {chloroplasts.map((pos, i) => {
        const delay = i * 15;
        const appear = interpolate(frame, [delay, delay + 30], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const innerPulse = 0.8 + Math.sin((frame + i * 10) / 20) * 0.1;

        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: `${pos.x}%`,
              top: `${pos.y}%`,
              width: 60,
              height: 30,
              background: "linear-gradient(90deg, #2E7D32, #4CAF50, #2E7D32)",
              borderRadius: "50%",
              transform: `translate(-50%, -50%) scale(${appear})`,
              boxShadow: `0 0 ${20 * innerPulse}px rgba(76, 175, 80, 0.6)`,
            }}
          >
            {/* Inner thylakoids */}
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: "20%",
                right: "20%",
                height: 3,
                background: "#1B5E20",
                transform: "translateY(-50%)",
              }}
            />
          </div>
        );
      })}

      <AnimatedText
        text="Chloroplasts"
        position="top"
        color="#2E7D32"
        fontSize={56}
        startFrame={45}
        endFrame={durationFrames - 30}
      />

      <AnimatedText
        text="Contain chlorophyll - the green pigment"
        position="bottom"
        color="#1B5E20"
        fontSize={32}
        startFrame={150}
        endFrame={durationFrames - 30}
      />
    </AbsoluteFill>
  );
};

// Scene 3: Process - The chemical reaction
const ProcessScene: React.FC<{ durationFrames: number }> = ({ durationFrames }) => {
  const frame = useCurrentFrame();

  // Arrow progress
  const arrowProgress = interpolate(frame, [120, 240], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Product appearance
  const productAppear = interpolate(frame, [250, 300], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: "linear-gradient(to bottom, #FFF8E1 0%, #FFECB3 100%)" }}>
      <AnimatedSun x={50} y={20} size={80} intensity={1.5} />

      {/* Reactants (left side) */}
      <Molecule type="co2" x={20} y={45} delay={30} />
      <Molecule type="co2" x={25} y={55} delay={45} />
      <Molecule type="h2o" x={18} y={65} delay={60} />
      <Molecule type="h2o" x={28} y={70} delay={75} />

      {/* Arrow */}
      <FlowArrow x1={35} y1={55} x2={60} y2={55} progress={arrowProgress} />

      {/* Products (right side) */}
      <div style={{ opacity: productAppear }}>
        <Molecule type="glucose" x={75} y={50} scale={1.2} />
        <Molecule type="o2" x={80} y={65} />
        <Molecule type="o2" x={70} y={70} />
      </div>

      <AnimatedText
        text="The Chemical Reaction"
        position="top"
        color="#F57F17"
        fontSize={52}
        startFrame={30}
        endFrame={200}
      />

      <AnimatedText
        text="CO₂ + H₂O → Glucose + O₂"
        position="center"
        color="#333"
        fontSize={44}
        startFrame={150}
        endFrame={durationFrames - 30}
      />

      <AnimatedText
        text="Sunlight provides the energy"
        position="bottom"
        color="#FF8F00"
        fontSize={32}
        startFrame={280}
        endFrame={durationFrames - 30}
      />
    </AbsoluteFill>
  );
};

// Scene 4: Conclusion - Why it matters
const ConclusionScene: React.FC<{ durationFrames: number }> = ({ durationFrames }) => {
  const frame = useCurrentFrame();

  // Multiple plants growing
  const growth1 = interpolate(frame, [0, 200], [0.3, 1], { extrapolateRight: "clamp" });
  const growth2 = interpolate(frame, [30, 230], [0.2, 0.9], { extrapolateRight: "clamp" });
  const growth3 = interpolate(frame, [60, 260], [0.1, 0.85], { extrapolateRight: "clamp" });

  // Oxygen bubbles rising
  const bubbles = [...Array(8)].map((_, i) => ({
    x: 20 + i * 10,
    baseY: 80 - (frame + i * 20) % 100,
    size: 8 + (i % 3) * 4,
  }));

  return (
    <AbsoluteFill style={{ background: "linear-gradient(to bottom, #81D4FA 0%, #B3E5FC 50%, #C8E6C9 100%)" }}>
      <AnimatedSun x={80} y={15} size={100} />

      {/* Ground */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: "30%",
          background: "linear-gradient(to bottom, #4CAF50, #2E7D32)",
        }}
      />

      {/* Forest of plants */}
      <AnimatedPlant x={25} y={30} growth={growth1} scale={1.5} />
      <AnimatedPlant x={50} y={30} growth={growth2} scale={1.8} />
      <AnimatedPlant x={75} y={30} growth={growth3} scale={1.3} />

      {/* Oxygen bubbles */}
      {bubbles.map((bubble, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: `${bubble.x}%`,
            bottom: `${bubble.baseY}%`,
            width: bubble.size,
            height: bubble.size,
            borderRadius: "50%",
            background: "rgba(255, 255, 255, 0.6)",
            border: "1px solid rgba(255, 255, 255, 0.8)",
          }}
        />
      ))}

      <AnimatedText
        text="Why It Matters"
        position="top"
        color="#1B5E20"
        fontSize={58}
        startFrame={30}
        endFrame={durationFrames - 30}
      />

      <AnimatedText
        text="Plants sustain all life on Earth"
        position="bottom"
        color="#ffffff"
        fontSize={42}
        startFrame={120}
        endFrame={durationFrames - 30}
      />
    </AbsoluteFill>
  );
};

// ============================================================================
// MAIN COMPOSITION
// ============================================================================

export interface PhotosynthesisProps {
  audioUrls?: {
    hook?: string;
    concept?: string;
    process?: string;
    conclusion?: string;
    backgroundMusic?: string;
  };
  backgroundMusicVolume?: number;
}

export const PhotosynthesisAnimation: React.FC<PhotosynthesisProps> = ({
  audioUrls = {},
  backgroundMusicVolume = 0.3,
}) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();

  // Scene timing (15 seconds each = 450 frames at 30fps)
  const sceneDuration = 450;

  // Background music fade out
  const musicVolume = interpolate(
    frame,
    [durationInFrames - fps * 2, durationInFrames],
    [backgroundMusicVolume, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Background music */}
      {audioUrls.backgroundMusic && (
        <Audio src={audioUrls.backgroundMusic} volume={musicVolume} />
      )}

      {/* Scene 1: Hook */}
      <Sequence from={0} durationInFrames={sceneDuration} name="Hook">
        <HookScene durationFrames={sceneDuration} />
        {audioUrls.hook && <Audio src={audioUrls.hook} />}
      </Sequence>

      {/* Scene 2: Concept */}
      <Sequence from={sceneDuration} durationInFrames={sceneDuration} name="Concept">
        <ConceptScene durationFrames={sceneDuration} />
        {audioUrls.concept && <Audio src={audioUrls.concept} />}
      </Sequence>

      {/* Scene 3: Process */}
      <Sequence from={sceneDuration * 2} durationInFrames={sceneDuration} name="Process">
        <ProcessScene durationFrames={sceneDuration} />
        {audioUrls.process && <Audio src={audioUrls.process} />}
      </Sequence>

      {/* Scene 4: Conclusion */}
      <Sequence from={sceneDuration * 3} durationInFrames={sceneDuration} name="Conclusion">
        <ConclusionScene durationFrames={sceneDuration} />
        {audioUrls.conclusion && <Audio src={audioUrls.conclusion} />}
      </Sequence>

      {/* Letterbox */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "8%", background: "black" }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "8%", background: "black" }} />
    </AbsoluteFill>
  );
};
