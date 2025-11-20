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
// TYPES
// ============================================================================

interface TextOverlayData {
  text: string;
  position: "top" | "center" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right";
  startFrame: number;
  endFrame: number;
  animation: "fadeIn" | "slideUp" | "slideDown" | "typewriter" | "scale" | "blur";
  style?: {
    fontSize?: number;
    color?: string;
    fontWeight?: string;
  };
}

interface SceneData {
  id: string;
  background: string;
  elements: string[];
  textOverlays: TextOverlayData[];
}

interface AudioFileData {
  part: string;
  url: string;
  duration: number;
}

interface AnimationData {
  title: string;
  scenes: SceneData[];
  audio_data: {
    audio_files: AudioFileData[];
    background_music: {
      url: string;
      duration: number;
    };
  };
}

export interface EducationalAnimationProps {
  animationData: AnimationData;
  backgroundMusicVolume?: number;
}

// ============================================================================
// ENHANCED ANIMATED COMPONENTS
// ============================================================================

// Realistic Sun with lens flare and better rays
const AnimatedSun: React.FC<{ x: number; y: number; size: number }> = ({ x, y, size }) => {
  const frame = useCurrentFrame();
  const glowPulse = 1 + Math.sin(frame / 25) * 0.08;
  const rayRotation = frame * 0.3;
  const coronaPulse = 1 + Math.sin(frame / 15) * 0.05;

  return (
    <div style={{ position: "absolute", left: `${x}%`, top: `${y}%`, transform: "translate(-50%, -50%)" }}>
      {/* Outer corona */}
      <div style={{
        position: "absolute", width: size * 4, height: size * 4, borderRadius: "50%",
        background: `radial-gradient(circle, rgba(255, 200, 50, 0.15) 0%, rgba(255, 150, 0, 0.05) 40%, transparent 70%)`,
        transform: `translate(-50%, -50%) scale(${coronaPulse})`, left: "50%", top: "50%",
        filter: "blur(20px)",
      }} />
      {/* Inner glow */}
      <div style={{
        position: "absolute", width: size * 2.5, height: size * 2.5, borderRadius: "50%",
        background: `radial-gradient(circle, rgba(255, 230, 100, 0.4) 0%, rgba(255, 180, 0, 0.1) 50%, transparent 70%)`,
        transform: `translate(-50%, -50%) scale(${glowPulse})`, left: "50%", top: "50%",
        filter: "blur(10px)",
      }} />
      {/* Sun body */}
      <div style={{
        width: size, height: size, borderRadius: "50%",
        background: "radial-gradient(circle at 30% 30%, #FFF5B8 0%, #FFE066 30%, #FFB300 70%, #FF8F00 100%)",
        boxShadow: `0 0 ${size}px rgba(255, 180, 0, 0.6), 0 0 ${size * 2}px rgba(255, 150, 0, 0.3), inset -${size/10}px -${size/10}px ${size/3}px rgba(255, 100, 0, 0.3)`,
      }} />
      {/* Light rays */}
      {[...Array(12)].map((_, i) => (
        <div key={i} style={{
          position: "absolute", left: "50%", top: "50%", width: 3, height: size * 1.2,
          background: `linear-gradient(to top, rgba(255, 230, 100, 0.8), rgba(255, 200, 50, 0.3), transparent)`,
          transformOrigin: "bottom center",
          transform: `translateX(-50%) rotate(${rayRotation + i * 30}deg) translateY(-${size * 0.6}px)`,
          opacity: 0.6,
          filter: "blur(1px)",
        }} />
      ))}
      {/* Lens flare */}
      <div style={{
        position: "absolute", width: size * 0.3, height: size * 0.3, borderRadius: "50%",
        background: "rgba(255, 255, 255, 0.8)",
        left: "25%", top: "25%", filter: "blur(2px)",
      }} />
    </div>
  );
};

// Enhanced plant with realistic leaves and details
const AnimatedPlant: React.FC<{ x: number; y: number; growth: number; scale?: number }> = ({ x, y, growth, scale = 1 }) => {
  const frame = useCurrentFrame();
  const sway = Math.sin(frame / 50) * 2;
  const stemHeight = 120 * growth;
  const leafSize = 50 * growth;

  return (
    <div style={{
      position: "absolute", left: `${x}%`, bottom: `${y}%`,
      transform: `translateX(-50%) rotate(${sway}deg) scale(${scale})`, transformOrigin: "bottom center",
    }}>
      {/* Main stem with gradient */}
      <div style={{
        width: 12, height: stemHeight,
        background: "linear-gradient(to right, #1B5E20, #2E7D32, #388E3C, #2E7D32, #1B5E20)",
        borderRadius: 6, position: "absolute", bottom: 0, left: "50%", transform: "translateX(-50%)",
        boxShadow: "2px 0 4px rgba(0,0,0,0.2)",
      }} />

      {/* Leaves at different heights */}
      {growth > 0.3 && (
        <>
          {/* Left leaf */}
          <div style={{
            position: "absolute", bottom: stemHeight * 0.5, left: "50%",
            width: leafSize * 1.2, height: leafSize * 0.5,
            background: "linear-gradient(135deg, #81C784 0%, #66BB6A 30%, #4CAF50 70%, #388E3C 100%)",
            borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
            transform: `translateX(-100%) rotate(-25deg)`, transformOrigin: "right center",
            boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
          }}>
            {/* Leaf vein */}
            <div style={{
              position: "absolute", top: "50%", left: "20%", right: "10%", height: 2,
              background: "rgba(27, 94, 32, 0.5)", transform: "translateY(-50%)",
            }} />
          </div>
          {/* Right leaf */}
          <div style={{
            position: "absolute", bottom: stemHeight * 0.5, left: "50%",
            width: leafSize * 1.2, height: leafSize * 0.5,
            background: "linear-gradient(225deg, #81C784 0%, #66BB6A 30%, #4CAF50 70%, #388E3C 100%)",
            borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
            transform: `rotate(25deg)`, transformOrigin: "left center",
            boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
          }}>
            <div style={{
              position: "absolute", top: "50%", left: "10%", right: "20%", height: 2,
              background: "rgba(27, 94, 32, 0.5)", transform: "translateY(-50%)",
            }} />
          </div>
        </>
      )}

      {/* Upper leaves */}
      {growth > 0.6 && (
        <>
          <div style={{
            position: "absolute", bottom: stemHeight * 0.75, left: "50%",
            width: leafSize, height: leafSize * 0.4,
            background: "linear-gradient(135deg, #A5D6A7 0%, #81C784 50%, #66BB6A 100%)",
            borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
            transform: `translateX(-100%) rotate(-35deg)`, transformOrigin: "right center",
            boxShadow: "0 2px 4px rgba(0,0,0,0.15)",
          }} />
          <div style={{
            position: "absolute", bottom: stemHeight * 0.75, left: "50%",
            width: leafSize, height: leafSize * 0.4,
            background: "linear-gradient(225deg, #A5D6A7 0%, #81C784 50%, #66BB6A 100%)",
            borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
            transform: `rotate(35deg)`, transformOrigin: "left center",
            boxShadow: "0 2px 4px rgba(0,0,0,0.15)",
          }} />
        </>
      )}

      {/* Top crown */}
      {growth > 0.8 && (
        <div style={{
          position: "absolute", bottom: stemHeight * 0.95, left: "50%",
          width: leafSize * 1.4, height: leafSize * 0.6,
          background: "radial-gradient(ellipse at center, #C8E6C9 0%, #A5D6A7 40%, #81C784 100%)",
          borderRadius: "50% 50% 50% 50% / 60% 60% 40% 40%",
          transform: `translateX(-50%)`,
          boxShadow: "0 3px 6px rgba(0,0,0,0.2)",
        }} />
      )}
    </div>
  );
};

// Realistic teacher with better proportions and details
const Teacher: React.FC<{ x: number; talking?: boolean }> = ({ x, talking = false }) => {
  const frame = useCurrentFrame();
  const headBob = talking ? Math.sin(frame / 10) * 1.5 : 0;
  const armGesture = talking ? Math.sin(frame / 12) * 8 : 0;
  const breathe = Math.sin(frame / 40) * 1;

  return (
    <div style={{ position: "absolute", left: `${x}%`, bottom: "12%", transform: "translateX(-50%)" }}>
      {/* Shadow */}
      <div style={{
        position: "absolute", bottom: -5, left: "50%", transform: "translateX(-50%)",
        width: 80, height: 15, background: "rgba(0,0,0,0.2)", borderRadius: "50%", filter: "blur(5px)",
      }} />

      {/* Legs */}
      <div style={{
        position: "absolute", bottom: 0, left: 15, width: 18, height: 50,
        background: "linear-gradient(to right, #37474F, #455A64, #37474F)",
        borderRadius: "0 0 4px 4px",
      }} />
      <div style={{
        position: "absolute", bottom: 0, left: 37, width: 18, height: 50,
        background: "linear-gradient(to right, #37474F, #455A64, #37474F)",
        borderRadius: "0 0 4px 4px",
      }} />

      {/* Body/Shirt */}
      <div style={{
        width: 70, height: 90,
        background: "linear-gradient(135deg, #5C6BC0 0%, #3F51B5 50%, #3949AB 100%)",
        borderRadius: "12px 12px 0 0", position: "absolute", bottom: 45,
        transform: `scaleY(${1 + breathe * 0.01})`, transformOrigin: "bottom",
        boxShadow: "0 4px 8px rgba(0,0,0,0.3)",
      }}>
        {/* Collar */}
        <div style={{
          position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)",
          width: 0, height: 0, borderLeft: "15px solid transparent", borderRight: "15px solid transparent",
          borderTop: "20px solid #E8EAF6",
        }} />
      </div>

      {/* Neck */}
      <div style={{
        position: "absolute", bottom: 130, left: "50%", transform: "translateX(-50%)",
        width: 20, height: 15, background: "#FFCC80",
      }} />

      {/* Head */}
      <div style={{
        width: 55, height: 60, background: "linear-gradient(135deg, #FFE0B2 0%, #FFCC80 50%, #FFB74D 100%)",
        borderRadius: "50% 50% 45% 45%",
        position: "absolute", bottom: 140, left: "50%", transform: `translateX(-50%) translateY(${headBob}px)`,
        boxShadow: "0 3px 6px rgba(0,0,0,0.2)",
      }}>
        {/* Hair */}
        <div style={{
          width: 55, height: 30,
          background: "linear-gradient(to bottom, #3E2723 0%, #4E342E 50%, #5D4037 100%)",
          borderRadius: "28px 28px 0 0",
          position: "absolute", top: 0,
        }} />
        {/* Eyes */}
        <div style={{ position: "absolute", top: 28, left: 12, width: 8, height: 8, background: "#333", borderRadius: "50%" }}>
          <div style={{ position: "absolute", top: 1, left: 2, width: 3, height: 3, background: "#fff", borderRadius: "50%" }} />
        </div>
        <div style={{ position: "absolute", top: 28, right: 12, width: 8, height: 8, background: "#333", borderRadius: "50%" }}>
          <div style={{ position: "absolute", top: 1, left: 2, width: 3, height: 3, background: "#fff", borderRadius: "50%" }} />
        </div>
        {/* Nose */}
        <div style={{
          position: "absolute", top: 32, left: "50%", transform: "translateX(-50%)",
          width: 6, height: 10, background: "#FFAB91", borderRadius: "50%",
        }} />
        {/* Mouth */}
        {talking ? (
          <div style={{
            position: "absolute", bottom: 10, left: "50%", transform: "translateX(-50%)",
            width: 12, height: 8, background: "#5D4037", borderRadius: "50%",
          }} />
        ) : (
          <div style={{
            position: "absolute", bottom: 12, left: "50%", transform: "translateX(-50%)",
            width: 15, height: 3, background: "#A1887F", borderRadius: "2px",
          }} />
        )}
      </div>

      {/* Pointing arm */}
      <div style={{
        width: 55, height: 14,
        background: "linear-gradient(to right, #5C6BC0, #3F51B5)",
        borderRadius: 7, position: "absolute", bottom: 110, left: 55,
        transform: `rotate(${-25 + armGesture}deg)`, transformOrigin: "left center",
        boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
      }}>
        {/* Hand */}
        <div style={{
          position: "absolute", right: -8, top: "50%", transform: "translateY(-50%)",
          width: 16, height: 16, background: "#FFCC80", borderRadius: "50%",
        }} />
      </div>
    </div>
  );
};

// Enhanced student with more detail
const Student: React.FC<{ x: number; variant: number }> = ({ x, variant }) => {
  const frame = useCurrentFrame();
  const colors = ["#EF5350", "#42A5F5", "#66BB6A", "#FFA726", "#AB47BC"];
  const hairColors = ["#3E2723", "#5D4037", "#212121", "#795548"];
  const skinTones = ["#FFCC80", "#FFE0B2", "#D7CCC8", "#FFAB91"];
  const bodyColor = colors[variant % colors.length];
  const hairColor = hairColors[variant % hairColors.length];
  const skinTone = skinTones[variant % skinTones.length];

  const headTilt = Math.sin((frame + variant * 20) / 35) * 2;
  const breathe = Math.sin((frame + variant * 10) / 45) * 0.5;

  return (
    <div style={{ position: "absolute", left: `${x}%`, bottom: "8%", transform: "translateX(-50%) scale(0.75)" }}>
      {/* Shadow */}
      <div style={{
        position: "absolute", bottom: -3, left: "50%", transform: "translateX(-50%)",
        width: 50, height: 10, background: "rgba(0,0,0,0.15)", borderRadius: "50%", filter: "blur(3px)",
      }} />

      {/* Body */}
      <div style={{
        width: 45, height: 65,
        background: `linear-gradient(135deg, ${bodyColor} 0%, ${bodyColor}dd 100%)`,
        borderRadius: "10px 10px 0 0", position: "absolute", bottom: 0,
        transform: `scaleY(${1 + breathe * 0.01})`, transformOrigin: "bottom",
        boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
      }} />

      {/* Neck */}
      <div style={{
        position: "absolute", bottom: 62, left: "50%", transform: "translateX(-50%)",
        width: 14, height: 8, background: skinTone,
      }} />

      {/* Head */}
      <div style={{
        width: 40, height: 42, background: `linear-gradient(135deg, ${skinTone} 0%, ${skinTone}dd 100%)`,
        borderRadius: "50% 50% 45% 45%",
        position: "absolute", bottom: 68, left: "50%",
        transform: `translateX(-50%) rotate(${headTilt}deg)`,
        boxShadow: "0 2px 4px rgba(0,0,0,0.15)",
      }}>
        {/* Hair */}
        <div style={{
          width: 40, height: 22, background: `linear-gradient(to bottom, ${hairColor}, ${hairColor}cc)`,
          borderRadius: "20px 20px 0 0", position: "absolute", top: 0,
        }} />
        {/* Eyes */}
        <div style={{ position: "absolute", top: 20, left: 8, width: 5, height: 5, background: "#333", borderRadius: "50%" }} />
        <div style={{ position: "absolute", top: 20, right: 8, width: 5, height: 5, background: "#333", borderRadius: "50%" }} />
      </div>
    </div>
  );
};

// Enhanced Whiteboard
const Whiteboard: React.FC<{ content?: string }> = ({ content }) => {
  return (
    <div style={{
      position: "absolute", top: "8%", left: "50%", transform: "translateX(-50%)",
      width: "65%", height: "42%",
      background: "linear-gradient(135deg, #FAFAFA 0%, #F5F5F5 50%, #EEEEEE 100%)",
      border: "12px solid #6D4C41",
      borderRadius: 6,
      boxShadow: "0 8px 24px rgba(0,0,0,0.3), inset 0 0 30px rgba(0,0,0,0.05)",
    }}>
      {/* Marker tray */}
      <div style={{
        position: "absolute", bottom: -25, left: "50%", transform: "translateX(-50%)",
        width: "80%", height: 12, background: "#8D6E63", borderRadius: "0 0 4px 4px",
        boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
      }} />
      {content && (
        <div style={{
          padding: 30, fontSize: 28, color: "#333", fontFamily: "system-ui",
          textAlign: "center", height: "100%", display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          {content}
        </div>
      )}
    </div>
  );
};

// Enhanced molecule with glow effects
const Molecule: React.FC<{ type: string; x: number; y: number; delay?: number }> = ({ type, x, y, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const localFrame = Math.max(0, frame - delay);
  const floatY = Math.sin(localFrame / 35) * 8;
  const floatX = Math.cos(localFrame / 45) * 5;
  const entrance = spring({ frame: localFrame, fps, config: { damping: 15, stiffness: 80, mass: 0.8 } });
  const glow = 0.5 + Math.sin(localFrame / 20) * 0.3;

  const getAtoms = () => {
    switch (type) {
      case "co2":
        return (
          <>
            <defs>
              <radialGradient id="carbon" cx="30%" cy="30%">
                <stop offset="0%" stopColor="#666" />
                <stop offset="100%" stopColor="#333" />
              </radialGradient>
              <radialGradient id="oxygen" cx="30%" cy="30%">
                <stop offset="0%" stopColor="#ff6666" />
                <stop offset="100%" stopColor="#cc0000" />
              </radialGradient>
            </defs>
            <circle cx="30" cy="25" r="14" fill="url(#carbon)" />
            <circle cx="52" cy="25" r="10" fill="url(#oxygen)" />
            <circle cx="8" cy="25" r="10" fill="url(#oxygen)" />
          </>
        );
      case "h2o":
        return (
          <>
            <defs>
              <radialGradient id="oxygenW" cx="30%" cy="30%">
                <stop offset="0%" stopColor="#6699ff" />
                <stop offset="100%" stopColor="#0044cc" />
              </radialGradient>
              <radialGradient id="hydrogen" cx="30%" cy="30%">
                <stop offset="0%" stopColor="#ffffff" />
                <stop offset="100%" stopColor="#cccccc" />
              </radialGradient>
            </defs>
            <circle cx="30" cy="18" r="12" fill="url(#oxygenW)" />
            <circle cx="16" cy="35" r="7" fill="url(#hydrogen)" />
            <circle cx="44" cy="35" r="7" fill="url(#hydrogen)" />
          </>
        );
      case "o2":
        return (
          <>
            <defs>
              <radialGradient id="o2grad" cx="30%" cy="30%">
                <stop offset="0%" stopColor="#ff8888" />
                <stop offset="100%" stopColor="#cc3333" />
              </radialGradient>
            </defs>
            <circle cx="18" cy="25" r="12" fill="url(#o2grad)" />
            <circle cx="42" cy="25" r="12" fill="url(#o2grad)" />
          </>
        );
      case "glucose":
        return (
          <>
            <polygon
              points="30,8 48,18 48,38 30,48 12,38 12,18"
              fill="none" stroke="#2E7D32" strokeWidth="4"
              strokeLinejoin="round"
            />
            <circle cx="30" cy="28" r="4" fill="#4CAF50" />
          </>
        );
      default:
        return <circle cx="30" cy="25" r="15" fill="#888" />;
    }
  };

  return (
    <div style={{
      position: "absolute", left: `${x}%`, top: `${y}%`,
      transform: `translate(-50%, -50%) translate(${floatX}px, ${floatY}px) scale(${entrance})`,
      filter: `drop-shadow(0 0 ${8 * glow}px rgba(100, 200, 255, 0.5))`,
    }}>
      <svg width="60" height="55" viewBox="0 0 60 55">{getAtoms()}</svg>
    </div>
  );
};

// Enhanced Chloroplast with internal structure
const Chloroplast: React.FC<{ x: number; y: number; delay?: number }> = ({ x, y, delay = 0 }) => {
  const frame = useCurrentFrame();
  const localFrame = Math.max(0, frame - delay);
  const appear = interpolate(localFrame, [0, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pulse = 0.85 + Math.sin(localFrame / 25) * 0.08;
  const innerRotate = localFrame * 0.3;

  return (
    <div style={{
      position: "absolute", left: `${x}%`, top: `${y}%`, width: 80, height: 40,
      background: "linear-gradient(135deg, #1B5E20 0%, #2E7D32 30%, #4CAF50 70%, #2E7D32 100%)",
      borderRadius: "50%",
      transform: `translate(-50%, -50%) scale(${appear})`,
      boxShadow: `0 0 ${25 * pulse}px rgba(76, 175, 80, 0.5), 0 4px 8px rgba(0,0,0,0.3)`,
      overflow: "hidden",
    }}>
      {/* Internal thylakoid membranes */}
      {[...Array(4)].map((_, i) => (
        <div key={i} style={{
          position: "absolute",
          top: `${25 + i * 12}%`,
          left: "15%", right: "15%",
          height: 3,
          background: "linear-gradient(90deg, transparent, rgba(129, 199, 132, 0.6), transparent)",
          transform: `rotate(${innerRotate + i * 5}deg)`,
        }} />
      ))}
      {/* Grana stacks */}
      <div style={{
        position: "absolute", top: "30%", left: "25%", width: 12, height: 16,
        background: "rgba(27, 94, 32, 0.7)", borderRadius: 3,
      }} />
      <div style={{
        position: "absolute", top: "35%", right: "25%", width: 12, height: 16,
        background: "rgba(27, 94, 32, 0.7)", borderRadius: 3,
      }} />
    </div>
  );
};

// Text overlay with animation
const AnimatedText: React.FC<{
  overlay: TextOverlayData;
  durationFrames: number;
}> = ({ overlay, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const startFrame = Math.max(0, overlay.startFrame);
  const endFrame = Math.min(durationFrames, overlay.endFrame);

  if (frame < startFrame || frame > endFrame) return null;

  const localFrame = frame - startFrame;
  const duration = endFrame - startFrame;

  let opacity = 1;
  let translateY = 0;
  let scale = 1;
  let displayText = overlay.text;

  switch (overlay.animation) {
    case "fadeIn":
      opacity = interpolate(localFrame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
      if (localFrame > duration - 30) {
        opacity = interpolate(localFrame, [duration - 30, duration], [1, 0], { extrapolateLeft: "clamp" });
      }
      break;
    case "slideUp":
      translateY = interpolate(localFrame, [0, 30], [50, 0], { extrapolateRight: "clamp", easing: Easing.out(Easing.ease) });
      opacity = interpolate(localFrame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
      if (localFrame > duration - 30) {
        opacity = interpolate(localFrame, [duration - 30, duration], [1, 0], { extrapolateLeft: "clamp" });
      }
      break;
    case "slideDown":
      translateY = interpolate(localFrame, [0, 30], [-50, 0], { extrapolateRight: "clamp", easing: Easing.out(Easing.ease) });
      opacity = interpolate(localFrame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
      if (localFrame > duration - 30) {
        opacity = interpolate(localFrame, [duration - 30, duration], [1, 0], { extrapolateLeft: "clamp" });
      }
      break;
    case "scale":
      scale = spring({ frame: localFrame, fps, config: { damping: 12, stiffness: 100, mass: 0.5 } });
      if (localFrame > duration - 30) {
        opacity = interpolate(localFrame, [duration - 30, duration], [1, 0], { extrapolateLeft: "clamp" });
      }
      break;
    default:
      opacity = interpolate(localFrame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
  }

  const positionStyles: React.CSSProperties = {
    top: overlay.position.includes("top") ? "10%" : overlay.position === "center" ? "50%" : undefined,
    bottom: overlay.position.includes("bottom") ? "12%" : undefined,
    left: overlay.position.includes("left") ? "5%" : overlay.position.includes("right") ? undefined : "50%",
    right: overlay.position.includes("right") ? "5%" : undefined,
    transform: `${!overlay.position.includes("left") && !overlay.position.includes("right") ? "translateX(-50%)" : ""} ${overlay.position === "center" ? "translateY(-50%)" : ""} translateY(${translateY}px) scale(${scale})`,
  };

  const style = overlay.style || {};

  return (
    <div style={{
      position: "absolute", ...positionStyles,
      fontSize: style.fontSize || 48, fontWeight: (style.fontWeight as any) || "bold", color: style.color || "#ffffff",
      textShadow: "3px 3px 12px rgba(0,0,0,0.8), 0 0 30px rgba(0,0,0,0.4), 0 0 60px rgba(0,0,0,0.2)",
      fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
      opacity,
      whiteSpace: "nowrap",
      letterSpacing: "0.02em",
    }}>
      {displayText}
    </div>
  );
};

// ============================================================================
// SCENE RENDERER
// ============================================================================

const SceneRenderer: React.FC<{
  scene: SceneData;
  durationFrames: number;
  audioUrl?: string;
}> = ({ scene, durationFrames, audioUrl }) => {
  const frame = useCurrentFrame();

  // Enhanced backgrounds with depth
  const getBackground = () => {
    switch (scene.background) {
      case "classroom":
        return "linear-gradient(180deg, #ECEFF1 0%, #CFD8DC 100%)";
      case "sky":
        return "linear-gradient(180deg, #1E88E5 0%, #64B5F6 40%, #90CAF9 70%, #BBDEFB 100%)";
      case "cell":
        return "linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 50%, #A5D6A7 100%)";
      case "equation":
        return "linear-gradient(180deg, #FFF8E1 0%, #FFECB3 100%)";
      case "forest":
        return "linear-gradient(180deg, #4FC3F7 0%, #81D4FA 30%, #B3E5FC 50%, #C8E6C9 70%, #A5D6A7 100%)";
      default:
        return "#1a1a2e";
    }
  };

  // Render elements based on scene data
  const renderElements = () => {
    const elements: React.ReactNode[] = [];

    scene.elements.forEach((element, i) => {
      switch (element) {
        case "sun":
          elements.push(<AnimatedSun key={`sun-${i}`} x={80} y={15} size={100} />);
          break;
        case "plant":
          const growth = interpolate(frame, [30, durationFrames - 30], [0.1, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          elements.push(<AnimatedPlant key={`plant-${i}`} x={50} y={28} growth={growth} scale={2.5} />);
          break;
        case "plants":
          const g1 = interpolate(frame, [0, 180], [0.3, 1], { extrapolateRight: "clamp" });
          const g2 = interpolate(frame, [20, 200], [0.2, 0.95], { extrapolateRight: "clamp" });
          const g3 = interpolate(frame, [40, 220], [0.15, 0.9], { extrapolateRight: "clamp" });
          elements.push(<AnimatedPlant key="p1" x={20} y={28} growth={g1} scale={1.8} />);
          elements.push(<AnimatedPlant key="p2" x={50} y={28} growth={g2} scale={2.2} />);
          elements.push(<AnimatedPlant key="p3" x={80} y={28} growth={g3} scale={1.6} />);
          break;
        case "teacher":
          elements.push(<Teacher key={`teacher-${i}`} x={18} talking={frame > 30} />);
          break;
        case "students":
          elements.push(<Student key="s1" x={45} variant={0} />);
          elements.push(<Student key="s2" x={58} variant={1} />);
          elements.push(<Student key="s3" x={71} variant={2} />);
          elements.push(<Student key="s4" x={84} variant={3} />);
          break;
        case "whiteboard":
          elements.push(<Whiteboard key={`wb-${i}`} />);
          break;
        case "chloroplasts":
          elements.push(<Chloroplast key="c1" x={30} y={40} delay={0} />);
          elements.push(<Chloroplast key="c2" x={55} y={32} delay={20} />);
          elements.push(<Chloroplast key="c3" x={40} y={58} delay={40} />);
          elements.push(<Chloroplast key="c4" x={65} y={52} delay={60} />);
          elements.push(<Chloroplast key="c5" x={48} y={70} delay={80} />);
          break;
        case "molecules":
          elements.push(<Molecule key="m1" type="co2" x={15} y={40} delay={30} />);
          elements.push(<Molecule key="m2" type="h2o" x={20} y={60} delay={60} />);
          elements.push(<Molecule key="m3" type="co2" x={12} y={75} delay={90} />);
          elements.push(<Molecule key="m4" type="glucose" x={80} y={45} delay={150} />);
          elements.push(<Molecule key="m5" type="o2" x={85} y={65} delay={180} />);
          elements.push(<Molecule key="m6" type="o2" x={78} y={80} delay={210} />);
          break;
        case "bubbles":
          [...Array(10)].map((_, j) => {
            const bubbleY = 85 - ((frame * 0.5 + j * 15) % 100);
            const bubbleX = 15 + j * 8 + Math.sin(frame / 20 + j) * 3;
            const size = 6 + (j % 4) * 3;
            elements.push(
              <div key={`bubble-${j}`} style={{
                position: "absolute", left: `${bubbleX}%`, bottom: `${bubbleY}%`,
                width: size, height: size, borderRadius: "50%",
                background: "radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.9), rgba(200, 230, 255, 0.4))",
                boxShadow: "inset -1px -1px 2px rgba(0,0,0,0.1)",
              }} />
            );
          });
          break;
        case "ground":
          elements.push(
            <div key={`ground-${i}`} style={{
              position: "absolute", bottom: 0, left: 0, right: 0, height: "28%",
              background: "linear-gradient(180deg, #8D6E63 0%, #6D4C41 30%, #5D4037 100%)",
              boxShadow: "inset 0 10px 30px rgba(0,0,0,0.3)",
            }}>
              {/* Grass tufts */}
              {[...Array(20)].map((_, j) => (
                <div key={`grass-${j}`} style={{
                  position: "absolute", bottom: "100%", left: `${j * 5 + 2}%`,
                  width: 0, height: 0,
                  borderLeft: "4px solid transparent", borderRight: "4px solid transparent",
                  borderBottom: `${15 + (j % 3) * 5}px solid #66BB6A`,
                  transform: `rotate(${Math.sin(j) * 10}deg)`,
                }} />
              ))}
            </div>
          );
          break;
        case "floor":
          elements.push(
            <div key={`floor-${i}`} style={{
              position: "absolute", bottom: 0, left: 0, right: 0, height: "12%",
              background: "linear-gradient(180deg, #A1887F 0%, #8D6E63 50%, #795548 100%)",
              boxShadow: "inset 0 5px 15px rgba(0,0,0,0.2)",
            }}>
              {/* Floor pattern */}
              {[...Array(12)].map((_, j) => (
                <div key={`tile-${j}`} style={{
                  position: "absolute", bottom: 0, left: `${j * 8.33}%`,
                  width: "8.33%", height: "100%",
                  borderRight: "1px solid rgba(0,0,0,0.1)",
                }} />
              ))}
            </div>
          );
          break;
      }
    });

    return elements;
  };

  return (
    <AbsoluteFill style={{ background: getBackground() }}>
      {renderElements()}

      {/* Text overlays */}
      {scene.textOverlays.map((overlay, index) => (
        <AnimatedText key={`text-${index}`} overlay={overlay} durationFrames={durationFrames} />
      ))}

      {/* Scene audio */}
      {audioUrl && <Audio src={audioUrl} />}
    </AbsoluteFill>
  );
};

// ============================================================================
// MAIN COMPOSITION
// ============================================================================

export const EducationalAnimation: React.FC<EducationalAnimationProps> = ({
  animationData,
  backgroundMusicVolume = 0.3,
}) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();

  const sceneDuration = Math.floor(durationInFrames / animationData.scenes.length);

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
      {animationData.audio_data?.background_music?.url && (
        <Audio src={animationData.audio_data.background_music.url} volume={musicVolume} />
      )}

      {/* Render each scene */}
      {animationData.scenes.map((scene, index) => {
        const audioFile = animationData.audio_data?.audio_files?.find(a => a.part === scene.id);

        return (
          <Sequence
            key={scene.id}
            from={index * sceneDuration}
            durationInFrames={sceneDuration}
            name={`Scene: ${scene.id}`}
          >
            <SceneRenderer
              scene={scene}
              durationFrames={sceneDuration}
              audioUrl={audioFile?.url}
            />
          </Sequence>
        );
      })}

      {/* Cinematic letterbox */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "6%", background: "black" }} />
      <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: "6%", background: "black" }} />
    </AbsoluteFill>
  );
};
