import { AbsoluteFill, Audio, Img, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring, staticFile } from "remotion";

// Types for the video composition props
export interface SceneData {
  part: string;
  imageUrl: string;
  audioUrl: string;
  startFrame: number;
  durationFrames: number;
  audioDurationFrames: number;
}

export interface VideoCompositionProps {
  scenes: SceneData[];
  backgroundMusicUrl?: string;
  backgroundMusicVolume?: number;
}

// Helper to get image source - use staticFile for local files, URL otherwise
const getImageSrc = (imageUrl: string): string => {
  // If it's a URL (starts with http), use it directly
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return imageUrl;
  }
  // Otherwise, it's a local file in the public folder
  return staticFile(imageUrl);
};

// Helper to get audio source - use staticFile for local files, URL otherwise
const getAudioSrc = (audioUrl: string): string => {
  if (!audioUrl) return '';
  // If it's a URL (starts with http), use it directly
  if (audioUrl.startsWith('http://') || audioUrl.startsWith('https://')) {
    return audioUrl;
  }
  // Otherwise, it's a local file in the public folder
  return staticFile(audioUrl);
};

// Individual scene component with Ken Burns effect
const Scene: React.FC<{
  imageUrl: string;
  audioUrl: string;
  audioDurationFrames: number;
  durationFrames: number;
}> = ({ imageUrl, audioUrl, audioDurationFrames, durationFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Ken Burns effect - slow zoom and pan
  const scale = interpolate(
    frame,
    [0, durationFrames],
    [1, 1.15],
    {
      extrapolateRight: "clamp",
    }
  );

  const translateX = interpolate(
    frame,
    [0, durationFrames],
    [0, -3],
    {
      extrapolateRight: "clamp",
    }
  );

  const translateY = interpolate(
    frame,
    [0, durationFrames],
    [0, -2],
    {
      extrapolateRight: "clamp",
    }
  );

  // Fade in effect
  const opacity = spring({
    frame,
    fps,
    config: {
      damping: 100,
      stiffness: 200,
      mass: 0.5,
    },
  });

  const imageSrc = getImageSrc(imageUrl);
  const audioSrc = getAudioSrc(audioUrl);

  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          transform: `scale(${scale}) translate(${translateX}%, ${translateY}%)`,
          opacity,
        }}
      >
        <Img
          src={imageSrc}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      </AbsoluteFill>
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
            audioUrl={scene.audioUrl}
            audioDurationFrames={scene.audioDurationFrames}
            durationFrames={scene.durationFrames}
          />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
