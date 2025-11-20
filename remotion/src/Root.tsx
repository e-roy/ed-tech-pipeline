import { Composition } from "remotion";
import { VideoComposition, VideoCompositionProps } from "./VideoComposition";
import { PhotosynthesisAnimation, PhotosynthesisProps } from "./PhotosynthesisAnimation";
import { EducationalAnimation, EducationalAnimationProps } from "./EducationalAnimation";

// Default props for studio preview
const defaultProps: VideoCompositionProps = {
  scenes: [
    {
      part: "hook",
      imageUrl: "https://via.placeholder.com/1920x1080/1a1a2e/ffffff?text=Hook",
      audioUrl: "",
      startFrame: 0,
      durationFrames: 360, // 12 seconds at 30fps
      audioDurationFrames: 132, // 4.4 seconds
    },
    {
      part: "concept",
      imageUrl: "https://via.placeholder.com/1920x1080/16213e/ffffff?text=Concept",
      audioUrl: "",
      startFrame: 360,
      durationFrames: 450, // 15 seconds
      audioDurationFrames: 228, // 7.6 seconds
    },
    {
      part: "process",
      imageUrl: "https://via.placeholder.com/1920x1080/0f3460/ffffff?text=Process",
      audioUrl: "",
      startFrame: 810,
      durationFrames: 660, // 22 seconds
      audioDurationFrames: 348, // 11.6 seconds
    },
    {
      part: "conclusion",
      imageUrl: "https://via.placeholder.com/1920x1080/533483/ffffff?text=Conclusion",
      audioUrl: "",
      startFrame: 1470,
      durationFrames: 330, // 11 seconds
      audioDurationFrames: 288, // 9.6 seconds
    },
  ],
  backgroundMusicUrl: "",
  backgroundMusicVolume: 0.3,
};

// Default props for PhotosynthesisAnimation
const photosynthesisDefaultProps: PhotosynthesisProps = {
  audioUrls: {},
  backgroundMusicVolume: 0.3,
};

// Default props for EducationalAnimation
const educationalDefaultProps: EducationalAnimationProps = {
  animationData: {
    title: "Demo",
    scenes: [
      {
        id: "intro",
        background: "classroom",
        elements: ["whiteboard", "teacher", "students", "floor"],
        textOverlays: [
          { text: "Welcome to Class!", position: "top", startFrame: 30, endFrame: 400, animation: "scale", style: { fontSize: 56, color: "#333" } }
        ]
      }
    ],
    audio_data: {
      audio_files: [],
      background_music: { url: "", duration: 60 }
    }
  },
  backgroundMusicVolume: 0.3,
};

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="VideoComposition"
        component={VideoComposition as unknown as React.FC<Record<string, unknown>>}
        durationInFrames={1800} // 60 seconds at 30fps
        fps={30}
        width={1920}
        height={1080}
        defaultProps={defaultProps}
      />
      <Composition
        id="PhotosynthesisAnimation"
        component={PhotosynthesisAnimation as unknown as React.FC<Record<string, unknown>>}
        durationInFrames={1800} // 60 seconds at 30fps (4 scenes x 15 seconds)
        fps={30}
        width={1920}
        height={1080}
        defaultProps={photosynthesisDefaultProps}
      />
      <Composition
        id="EducationalAnimation"
        component={EducationalAnimation as unknown as React.FC<Record<string, unknown>>}
        durationInFrames={1800} // 60 seconds at 30fps
        fps={30}
        width={1920}
        height={1080}
        defaultProps={educationalDefaultProps}
      />
    </>
  );
};
