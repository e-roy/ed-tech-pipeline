import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring, staticFile, Easing } from "remotion";
import React from "react";
import { DiagramConfig, DiagramRenderer } from "./DiagramComponents";

// Types for animation data
export interface CameraAnimation {
  startZoom: number;
  endZoom: number;
  startX: number;
  endX: number;
  startY: number;
  endY: number;
  easing: "linear" | "easeIn" | "easeOut" | "easeInOut" | "spring";
}

export interface TextOverlayStyle {
  fontSize?: number;
  color?: string;
  fontWeight?: "normal" | "bold";
  shadow?: boolean;
}

export interface TextOverlay {
  text: string;
  position: "top" | "center" | "bottom" | "top-left" | "top-right" | "bottom-left" | "bottom-right";
  startFrame: number;
  endFrame: number;
  animation: "fadeIn" | "slideUp" | "slideDown" | "typewriter" | "scale" | "blur";
  style?: TextOverlayStyle;
}

export interface ShapePosition {
  x: string;
  y: string;
  width: string;
  height: string;
}

export interface Shape {
  type: "rectangle" | "circle" | "line" | "gradient";
  color: string;
  opacity?: number;
  startFrame: number;
  endFrame: number;
  animation: "wipe" | "expand" | "pulse" | "slide";
  position?: ShapePosition;
}

export interface Effects {
  vignette?: boolean;
  vignetteIntensity?: number;
  colorGrade?: "none" | "warm" | "cool" | "dramatic" | "vintage";
  grain?: boolean;
  letterbox?: boolean;
}

export interface Transitions {
  in?: "fade" | "wipe" | "zoom" | "slide" | "blur";
  out?: "fade" | "wipe" | "zoom" | "slide" | "blur";
  inDuration?: number;
  outDuration?: number;
}

export interface AnimationData {
  camera?: CameraAnimation;
  textOverlays?: TextOverlay[];
  shapes?: Shape[];
  effects?: Effects;
  transitions?: Transitions;
}

// Types for the video composition props
export interface SceneData {
  part: string;
  imageUrl?: string;
  videoUrl?: string;
  visualType?: "video" | "image" | "diagram";
  diagram?: DiagramConfig;
  audioUrl: string;
  startFrame: number;
  durationFrames: number;
  audioDurationFrames: number;
  animation?: AnimationData;
}

export interface VideoCompositionProps {
  scenes: SceneData[];
  backgroundMusicUrl?: string;
  backgroundMusicVolume?: number;
}

// Helper to get image source - use staticFile for local files, URL otherwise
const getImageSrc = (imageUrl: string): string => {
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return imageUrl;
  }
  return staticFile(imageUrl);
};

// Helper to get audio source - use staticFile for local files, URL otherwise
const getAudioSrc = (audioUrl: string): string => {
  if (!audioUrl) return '';
  if (audioUrl.startsWith('http://') || audioUrl.startsWith('https://')) {
    return audioUrl;
  }
  return staticFile(audioUrl);
};

// Get easing function based on name
const getEasing = (easingName: string) => {
  switch (easingName) {
    case "easeIn":
      return Easing.in(Easing.ease);
    case "easeOut":
      return Easing.out(Easing.ease);
    case "easeInOut":
      return Easing.inOut(Easing.ease);
    default:
      return (t: number) => t; // linear
  }
};

// Get position styles for text overlays
const getPositionStyles = (position: string): React.CSSProperties => {
  const base: React.CSSProperties = {
    position: "absolute",
    display: "flex",
    padding: "20px",
  };

  switch (position) {
    case "top":
      return { ...base, top: "10%", left: "50%", transform: "translateX(-50%)", textAlign: "center" };
    case "center":
      return { ...base, top: "50%", left: "50%", transform: "translate(-50%, -50%)", textAlign: "center" };
    case "bottom":
      return { ...base, bottom: "15%", left: "50%", transform: "translateX(-50%)", textAlign: "center" };
    case "top-left":
      return { ...base, top: "10%", left: "5%" };
    case "top-right":
      return { ...base, top: "10%", right: "5%" };
    case "bottom-left":
      return { ...base, bottom: "15%", left: "5%" };
    case "bottom-right":
      return { ...base, bottom: "15%", right: "5%" };
    default:
      return { ...base, top: "50%", left: "50%", transform: "translate(-50%, -50%)" };
  }
};

// Text overlay component with animations
const AnimatedText: React.FC<{
  overlay: TextOverlay;
  durationFrames: number;
}> = ({ overlay, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Clamp frame values to scene duration
  const startFrame = Math.max(0, overlay.startFrame);
  const endFrame = Math.min(durationFrames, overlay.endFrame);

  // Check if text should be visible
  if (frame < startFrame || frame > endFrame) {
    return null;
  }

  const localFrame = frame - startFrame;
  const duration = endFrame - startFrame;

  // Animation values
  let opacity = 1;
  let translateY = 0;
  let scale = 1;
  let blur = 0;
  let displayText = overlay.text;

  switch (overlay.animation) {
    case "fadeIn":
      opacity = interpolate(localFrame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
      // Fade out at end
      if (localFrame > duration - 30) {
        opacity = interpolate(localFrame, [duration - 30, duration], [1, 0], { extrapolateLeft: "clamp" });
      }
      break;

    case "slideUp":
      translateY = interpolate(localFrame, [0, 30], [50, 0], {
        extrapolateRight: "clamp",
        easing: Easing.out(Easing.ease),
      });
      opacity = interpolate(localFrame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
      if (localFrame > duration - 30) {
        translateY = interpolate(localFrame, [duration - 30, duration], [0, -50], { extrapolateLeft: "clamp" });
        opacity = interpolate(localFrame, [duration - 30, duration], [1, 0], { extrapolateLeft: "clamp" });
      }
      break;

    case "slideDown":
      translateY = interpolate(localFrame, [0, 30], [-50, 0], {
        extrapolateRight: "clamp",
        easing: Easing.out(Easing.ease),
      });
      opacity = interpolate(localFrame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
      break;

    case "typewriter":
      const charsToShow = Math.floor(interpolate(localFrame, [0, duration * 0.6], [0, overlay.text.length], {
        extrapolateRight: "clamp",
      }));
      displayText = overlay.text.substring(0, charsToShow);
      opacity = localFrame > duration - 30
        ? interpolate(localFrame, [duration - 30, duration], [1, 0], { extrapolateLeft: "clamp" })
        : 1;
      break;

    case "scale":
      scale = spring({
        frame: localFrame,
        fps,
        config: { damping: 12, stiffness: 100, mass: 0.5 },
      });
      if (localFrame > duration - 30) {
        scale = interpolate(localFrame, [duration - 30, duration], [1, 0.8], { extrapolateLeft: "clamp" });
        opacity = interpolate(localFrame, [duration - 30, duration], [1, 0], { extrapolateLeft: "clamp" });
      }
      break;

    case "blur":
      blur = interpolate(localFrame, [0, 30], [10, 0], { extrapolateRight: "clamp" });
      opacity = interpolate(localFrame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
      break;
  }

  const style = overlay.style || {};
  const textStyle: React.CSSProperties = {
    fontSize: style.fontSize || 48,
    color: style.color || "white",
    fontWeight: style.fontWeight || "bold",
    fontFamily: "system-ui, -apple-system, sans-serif",
    textShadow: style.shadow !== false ? "2px 2px 8px rgba(0,0,0,0.8), 0 0 20px rgba(0,0,0,0.5)" : "none",
    opacity,
    transform: `translateY(${translateY}px) scale(${scale})`,
    filter: blur > 0 ? `blur(${blur}px)` : "none",
    whiteSpace: "nowrap",
  };

  return (
    <div style={getPositionStyles(overlay.position)}>
      <span style={textStyle}>{displayText}</span>
    </div>
  );
};

// Shape component with animations
const AnimatedShape: React.FC<{
  shape: Shape;
  durationFrames: number;
}> = ({ shape, durationFrames }) => {
  const frame = useCurrentFrame();

  const startFrame = Math.max(0, shape.startFrame);
  const endFrame = Math.min(durationFrames, shape.endFrame);

  if (frame < startFrame || frame > endFrame) {
    return null;
  }

  const localFrame = frame - startFrame;
  const duration = endFrame - startFrame;

  const position = shape.position || { x: "0", y: "0", width: "100%", height: "100%" };

  // Parse position values
  const parsePosition = (value: string): string => {
    if (value === "center") return "50%";
    return value;
  };

  let opacity = shape.opacity || 0.5;
  let scaleX = 1;
  let scaleY = 1;

  switch (shape.animation) {
    case "wipe":
      scaleX = interpolate(localFrame, [0, 60], [0, 1], { extrapolateRight: "clamp" });
      break;

    case "expand":
      const expandProgress = interpolate(localFrame, [0, 45], [0, 1], {
        extrapolateRight: "clamp",
        easing: Easing.out(Easing.ease),
      });
      scaleX = expandProgress;
      scaleY = expandProgress;
      break;

    case "pulse":
      const pulseValue = Math.sin((localFrame / 30) * Math.PI) * 0.1 + 0.9;
      opacity = (shape.opacity || 0.5) * pulseValue;
      break;

    case "slide":
      scaleX = interpolate(localFrame, [0, 30], [0, 1], { extrapolateRight: "clamp" });
      break;
  }

  const shapeStyle: React.CSSProperties = {
    position: "absolute",
    left: parsePosition(position.x),
    top: parsePosition(position.y),
    width: position.width,
    height: position.height,
    backgroundColor: shape.color,
    opacity,
    transform: `scaleX(${scaleX}) scaleY(${scaleY})`,
    transformOrigin: "left center",
    borderRadius: shape.type === "circle" ? "50%" : "0",
  };

  return <div style={shapeStyle} />;
};

// Effects layer component
const EffectsLayer: React.FC<{
  effects: Effects;
  durationFrames: number;
}> = ({ effects, durationFrames }) => {
  const frame = useCurrentFrame();

  return (
    <>
      {/* Vignette */}
      {effects.vignette && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: `radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,${effects.vignetteIntensity || 0.3}) 100%)`,
            pointerEvents: "none",
          }}
        />
      )}

      {/* Color grading */}
      {effects.colorGrade && effects.colorGrade !== "none" && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            mixBlendMode: "overlay",
            opacity: 0.3,
            background:
              effects.colorGrade === "warm" ? "rgba(255, 150, 100, 0.3)" :
              effects.colorGrade === "cool" ? "rgba(100, 150, 255, 0.3)" :
              effects.colorGrade === "dramatic" ? "rgba(30, 30, 60, 0.4)" :
              effects.colorGrade === "vintage" ? "rgba(255, 230, 180, 0.3)" :
              "transparent",
            pointerEvents: "none",
          }}
        />
      )}

      {/* Film grain */}
      {effects.grain && (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            opacity: 0.05,
            background: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
            pointerEvents: "none",
          }}
        />
      )}

      {/* Letterbox */}
      {effects.letterbox && (
        <>
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              height: "8%",
              background: "black",
            }}
          />
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              height: "8%",
              background: "black",
            }}
          />
        </>
      )}
    </>
  );
};

// Individual scene component with dynamic animations
const Scene: React.FC<{
  imageUrl?: string;
  videoUrl?: string;
  visualType?: "video" | "image" | "diagram";
  diagram?: DiagramConfig;
  audioUrl: string;
  audioDurationFrames: number;
  durationFrames: number;
  animation?: AnimationData;
}> = ({ imageUrl, videoUrl, visualType = "image", diagram, audioUrl, audioDurationFrames, durationFrames, animation }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Default animation if none provided
  const camera = animation?.camera || {
    startZoom: 1,
    endZoom: 1.15,
    startX: 0,
    endX: -3,
    startY: 0,
    endY: -2,
    easing: "easeInOut" as const,
  };

  const transitions = animation?.transitions || {
    in: "fade" as const,
    out: "fade" as const,
    inDuration: 15,
    outDuration: 15,
  };

  // Camera movement with easing
  const easing = getEasing(camera.easing);

  const scale = interpolate(
    frame,
    [0, durationFrames],
    [camera.startZoom, camera.endZoom],
    { extrapolateRight: "clamp", easing }
  );

  const translateX = interpolate(
    frame,
    [0, durationFrames],
    [camera.startX, camera.endX],
    { extrapolateRight: "clamp", easing }
  );

  const translateY = interpolate(
    frame,
    [0, durationFrames],
    [camera.startY, camera.endY],
    { extrapolateRight: "clamp", easing }
  );

  // Transition animations
  let transitionOpacity = 1;
  let transitionScale = 1;
  let transitionBlur = 0;
  let transitionX = 0;

  const inDuration = transitions.inDuration || 15;
  const outDuration = transitions.outDuration || 15;

  // Transition in
  if (frame < inDuration) {
    switch (transitions.in) {
      case "fade":
        transitionOpacity = interpolate(frame, [0, inDuration], [0, 1], { extrapolateRight: "clamp" });
        break;
      case "zoom":
        transitionScale = interpolate(frame, [0, inDuration], [1.3, 1], { extrapolateRight: "clamp" });
        transitionOpacity = interpolate(frame, [0, inDuration], [0, 1], { extrapolateRight: "clamp" });
        break;
      case "slide":
        transitionX = interpolate(frame, [0, inDuration], [100, 0], { extrapolateRight: "clamp" });
        break;
      case "blur":
        transitionBlur = interpolate(frame, [0, inDuration], [20, 0], { extrapolateRight: "clamp" });
        transitionOpacity = interpolate(frame, [0, inDuration], [0, 1], { extrapolateRight: "clamp" });
        break;
      case "wipe":
        // Handled separately
        break;
    }
  }

  // Transition out
  if (frame > durationFrames - outDuration) {
    switch (transitions.out) {
      case "fade":
        transitionOpacity = interpolate(frame, [durationFrames - outDuration, durationFrames], [1, 0], { extrapolateLeft: "clamp" });
        break;
      case "zoom":
        transitionScale = interpolate(frame, [durationFrames - outDuration, durationFrames], [1, 0.8], { extrapolateLeft: "clamp" });
        transitionOpacity = interpolate(frame, [durationFrames - outDuration, durationFrames], [1, 0], { extrapolateLeft: "clamp" });
        break;
      case "slide":
        transitionX = interpolate(frame, [durationFrames - outDuration, durationFrames], [0, -100], { extrapolateLeft: "clamp" });
        break;
      case "blur":
        transitionBlur = interpolate(frame, [durationFrames - outDuration, durationFrames], [0, 20], { extrapolateLeft: "clamp" });
        transitionOpacity = interpolate(frame, [durationFrames - outDuration, durationFrames], [1, 0], { extrapolateLeft: "clamp" });
        break;
    }
  }

  const imageSrc = imageUrl ? getImageSrc(imageUrl) : '';
  const audioSrc = getAudioSrc(audioUrl);

  // Determine visual mode
  const isVideoMode = visualType === "video" && videoUrl;
  const isDiagramMode = visualType === "diagram" && diagram;

  return (
    <AbsoluteFill>
      {/* Main visual layer */}
      {isDiagramMode ? (
        /* Diagram mode - render diagram component */
        <AbsoluteFill
          style={{
            opacity: transitionOpacity,
            filter: transitionBlur > 0 ? `blur(${transitionBlur}px)` : "none",
          }}
        >
          <DiagramRenderer config={diagram} />
        </AbsoluteFill>
      ) : isVideoMode ? (
        /* Video mode - render video clip without Ken Burns effect */
        <AbsoluteFill
          style={{
            opacity: transitionOpacity,
            filter: transitionBlur > 0 ? `blur(${transitionBlur}px)` : "none",
          }}
        >
          <OffthreadVideo
            src={videoUrl}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
            }}
          />
        </AbsoluteFill>
      ) : (
        /* Image mode - render with Ken Burns camera movement */
        <AbsoluteFill
          style={{
            transform: `scale(${scale * transitionScale}) translate(${translateX + transitionX}%, ${translateY}%)`,
            opacity: transitionOpacity,
            filter: transitionBlur > 0 ? `blur(${transitionBlur}px)` : "none",
          }}
        >
          {imageSrc && (
            <Img
              src={imageSrc}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
              }}
            />
          )}
        </AbsoluteFill>
      )}

      {/* Shapes layer */}
      {animation?.shapes?.map((shape, index) => (
        <AnimatedShape
          key={`shape-${index}`}
          shape={shape}
          durationFrames={durationFrames}
        />
      ))}

      {/* Effects layer */}
      {animation?.effects && (
        <EffectsLayer
          effects={animation.effects}
          durationFrames={durationFrames}
        />
      )}

      {/* Text overlays layer */}
      {animation?.textOverlays?.map((overlay, index) => (
        <AnimatedText
          key={`text-${index}`}
          overlay={overlay}
          durationFrames={durationFrames}
        />
      ))}

      {/* Audio */}
      {audioSrc && <Audio src={audioSrc} />}
    </AbsoluteFill>
  );
};

// Main composition
export const VideoComposition: React.FC<VideoCompositionProps> = ({
  scenes,
  backgroundMusicUrl,
  backgroundMusicVolume = 0.3,
}) => {
  const { fps, durationInFrames } = useVideoConfig();
  const frame = useCurrentFrame();

  // Fade out background music at the end
  const musicVolume = interpolate(
    frame,
    [durationInFrames - fps * 2, durationInFrames],
    [backgroundMusicVolume, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Background music layer */}
      {backgroundMusicUrl && (
        <Audio src={backgroundMusicUrl} volume={musicVolume} />
      )}

      {/* Scene sequences */}
      {scenes.map((scene, index) => (
        <Sequence
          key={scene.part}
          from={scene.startFrame}
          durationInFrames={scene.durationFrames}
          name={`Scene ${index + 1}: ${scene.part}`}
        >
          <Scene
            imageUrl={scene.imageUrl}
            videoUrl={scene.videoUrl}
            visualType={scene.visualType}
            diagram={scene.diagram}
            audioUrl={scene.audioUrl}
            audioDurationFrames={scene.audioDurationFrames}
            durationFrames={scene.durationFrames}
            animation={scene.animation}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
