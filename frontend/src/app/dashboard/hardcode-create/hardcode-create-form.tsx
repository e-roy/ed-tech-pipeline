"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface HardcodeCreateFormProps {
  userEmail: string;
  sessionId: string;
}

export function HardcodeCreateForm({
  userEmail,
  sessionId,
}: HardcodeCreateFormProps) {
  const [templateTitle, setTemplateTitle] = useState("Photosynthesis");
  const [hookText, setHookText] = useState(
    "Have you ever wondered how plants make their own food? Let's discover the amazing process of photosynthesis!",
  );
  const [conceptText, setConceptText] = useState(
    "Plants use a process called photosynthesis. Inside their leaves are tiny structures called chloroplasts that contain chlorophyll - the green pigment that captures sunlight.",
  );
  const [processText, setProcessText] = useState(
    "When sunlight hits the chlorophyll, it triggers a chemical reaction. The plant takes in carbon dioxide from the air and water from the soil, and converts them into glucose - that's sugar, the plant's food! The chemical equation is: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂",
  );
  const [conclusionText, setConclusionText] = useState(
    "As a bonus, plants release oxygen as a byproduct. That's the air we breathe! So next time you see a green plant, remember - it's a tiny food factory powered by the sun.",
  );
  const [hookVisualGuidance, setHookVisualGuidance] = useState(
    "Animated question mark with plant growing time-lapse",
  );
  const [conceptVisualGuidance, setConceptVisualGuidance] = useState(
    "Diagram of leaf → zoom to chloroplast → highlight chlorophyll",
  );
  const [processVisualGuidance, setProcessVisualGuidance] = useState(
    "Animated diagram showing CO₂ + H₂O → glucose + O₂ with arrows",
  );
  const [conclusionVisualGuidance, setConclusionVisualGuidance] = useState(
    "Real-world footage of child near tree, text overlay with key takeaway",
  );
  const [diagramFile, setDiagramFile] = useState<File | null>(null);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [numImages, setNumImages] = useState(2);
  const [maxPasses, setMaxPasses] = useState(5);
  const [maxVerificationPasses, setMaxVerificationPasses] = useState(3);
  const [fastMode, setFastMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState<number | null>(null);
  const [totalCost, setTotalCost] = useState<number | null>(null);
  const [statusItems, setStatusItems] = useState<any[]>([]);
  const [generatedImages, setGeneratedImages] = useState<any[]>([]);
  const [generatedAudio, setGeneratedAudio] = useState<any[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket connection for real-time updates
  const { isConnected, lastMessage } = useWebSocket(activeSessionId);

  // Function to fetch final results from API
  const fetchResults = async (sessionIdToFetch: string) => {
    try {
      console.log(
        "[HardcodeCreate] Fetching final results for session:",
        sessionIdToFetch,
      );
      const statusResponse = await fetch(
        `${API_URL}/api/story-images/${sessionIdToFetch}`,
        {
          headers: {
            "X-User-Email": userEmail,
          },
        },
      );

      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        console.log("[HardcodeCreate] Final results fetched:", statusData);
        setResults(statusData);
        setIsLoading(false);
        setSuccess(true);
        setProgress(null);

        // Clear polling interval if active
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      } else {
        console.error(
          "[HardcodeCreate] Failed to fetch results:",
          statusResponse.status,
        );
      }
    } catch (err) {
      console.error("[HardcodeCreate] Error fetching results:", err);
    }
  };

  // Listen for WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      console.log("[HardcodeCreate] WebSocket message received:", lastMessage);

      // Handle different message formats
      // Backend sends: { status, details, progress, elapsed_time, total_cost, items }
      // Or: { type: "assets_ready", images: [...], audio: [...] }
      const messageType = (lastMessage as any).type;
      const status = (lastMessage as any).status || lastMessage.stage;
      const message = (lastMessage as any).details || lastMessage.message;
      const progress = (lastMessage as any).progress;
      const elapsed = (lastMessage as any).elapsed_time;
      const cost = (lastMessage as any).total_cost;
      const items = (lastMessage as any).items;

      // Handle assets_ready message
      if (messageType === "assets_ready") {
        const images = (lastMessage as any).images || [];
        const audio = (lastMessage as any).audio || [];
        console.log("[HardcodeCreate] Assets ready:", { images, audio });
        setGeneratedImages(images);
        setGeneratedAudio(audio);
        return;
      }

      // Update elapsed time and cost if provided
      if (elapsed !== undefined) {
        setElapsedTime(elapsed);
      }
      if (cost !== undefined) {
        setTotalCost(cost);
      }

      // Update cumulative status items if provided
      if (items && Array.isArray(items)) {
        setStatusItems(items);
        console.log("[HardcodeCreate] Status items updated:", items);
      } else if (items === null) {
        // Clear status items when null (on completion)
        setStatusItems([]);
      }

      // Update progress display
      if (message) {
        setProgress(message);
        console.log("[HardcodeCreate] Progress update:", message);
      }

      // Check if images and audio generation is complete
      if (
        status === "images_audio_complete" ||
        status === "images_and_audio_generated"
      ) {
        console.log(
          "[HardcodeCreate] Images and audio complete! Status:",
          status,
        );
        setIsLoading(false);
        setSuccess(true);
        setProgress(null);
        // Optionally fetch full results from API
        fetchResults(lastMessage.session_id);
      }

      // Check if video composition is complete
      if (
        status === "hardcode_story_complete" ||
        status === "complete" ||
        status === "completed"
      ) {
        console.log("[HardcodeCreate] Video composition complete!");
        fetchResults(lastMessage.session_id);
      }

      // Handle errors
      if (status === "error" || status === "failed") {
        console.error("[HardcodeCreate] Error status received:", message);
        setIsLoading(false);
        setError(message || "Processing failed");
        setProgress(null);
      }
    }
  }, [lastMessage]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setDiagramFile(file);
    }
  };

  const generateSegmentsMd = () => {
    const segments = [
      {
        number: 1,
        title: "Hook",
        text: hookText,
        visualGuidance: hookVisualGuidance,
        duration: 10,
        start: 0,
        end: 10,
      },
      {
        number: 2,
        title: "Concept Introduction",
        text: conceptText,
        visualGuidance: conceptVisualGuidance,
        duration: 15,
        start: 10,
        end: 25,
      },
      {
        number: 3,
        title: "Process Explanation",
        text: processText,
        visualGuidance: processVisualGuidance,
        duration: 20,
        start: 25,
        end: 45,
      },
      {
        number: 4,
        title: "Conclusion",
        text: conclusionText,
        visualGuidance: conclusionVisualGuidance,
        duration: 15,
        start: 45,
        end: 60,
      },
    ];

    let content = `Template: ${templateTitle}\n\n`;
    for (const seg of segments) {
      content += `**Segment ${seg.number}: ${seg.title} (${seg.start}-${seg.end} seconds)**\n\n`;
      content += `- Narration text:\n  \`\`\`\n  ${seg.text}\n  \`\`\`\n`;
      content += `- Visual guidance preview: ${seg.visualGuidance}\n\n`;
    }
    return content;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(false);
    setProgress("Generating segments.md...");
    setGeneratedImages([]);
    setGeneratedAudio([]);
    setStatusItems([]);

    console.log("[HardcodeCreate] Form submission started");
    console.log("[HardcodeCreate] API_URL:", API_URL);
    console.log("[HardcodeCreate] Session ID:", sessionId);
    console.log("[HardcodeCreate] User Email:", userEmail);

    try {
      // User email is passed as prop from server component

      // Generate segments.md content
      const segmentsMdContent = generateSegmentsMd();
      console.log("[HardcodeCreate] Generated segments.md content");

      // Create FormData for file upload
      const formData = new FormData();
      formData.append("session_id", sessionId);
      formData.append("template_title", templateTitle);
      formData.append("hook_text", hookText);
      formData.append("concept_text", conceptText);
      formData.append("process_text", processText);
      formData.append("conclusion_text", conclusionText);
      formData.append("hook_visual_guidance", hookVisualGuidance);
      formData.append("concept_visual_guidance", conceptVisualGuidance);
      formData.append("process_visual_guidance", processVisualGuidance);
      formData.append("conclusion_visual_guidance", conclusionVisualGuidance);
      formData.append(
        "segments_md",
        new Blob([segmentsMdContent], { type: "text/markdown" }),
        "segments.md",
      );
      if (diagramFile) {
        formData.append("diagram", diagramFile);
        console.log(
          "[HardcodeCreate] Diagram file attached:",
          diagramFile.name,
        );
      }
      formData.append("num_images", numImages.toString());
      formData.append("max_passes", maxPasses.toString());
      formData.append(
        "max_verification_passes",
        maxVerificationPasses.toString(),
      );
      formData.append("fast_mode", fastMode.toString());

      console.log("[HardcodeCreate] FormData prepared");

      setProgress("Uploading files to S3...");

      // Upload files and trigger processing
      const uploadUrl = `${API_URL}/api/hardcode-upload`;
      console.log("[HardcodeCreate] POST request to:", uploadUrl);
      console.log("[HardcodeCreate] Request headers:", {
        "X-User-Email": userEmail,
      });

      const response = await fetch(uploadUrl, {
        method: "POST",
        headers: {
          "X-User-Email": userEmail,
        },
        body: formData,
      });

      console.log("[HardcodeCreate] Response status:", response.status);
      console.log("[HardcodeCreate] Response statusText:", response.statusText);
      console.log("[HardcodeCreate] Response ok:", response.ok);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("[HardcodeCreate] Upload failed with error:", errorData);
        throw new Error(
          errorData.detail || `Upload failed: ${response.statusText}`,
        );
      }

      const result = await response.json();
      console.log("[HardcodeCreate] Upload successful:", result);
      setProgress("Processing started! Generating images and audio...");

      // Activate WebSocket connection for real-time updates
      setActiveSessionId(sessionId);
      console.log(
        "[HardcodeCreate] Activated WebSocket for session:",
        sessionId,
      );
      console.log("[HardcodeCreate] Waiting for WebSocket updates...");
    } catch (err) {
      console.error(
        "[HardcodeCreate] Fatal error during form submission:",
        err,
      );
      setIsLoading(false);
      setError(err instanceof Error ? err.message : "An error occurred");
      setProgress(null);
    }
  };

  const handleComposeVideo = async () => {
    if (!sessionId) {
      setError("No session ID available");
      return;
    }

    try {
      console.log(
        "[HardcodeCreate] Starting video composition for session:",
        sessionId,
      );
      setIsLoading(true);
      setProgress("Starting video composition...");
      setError(null);

      const response = await fetch(
        `${API_URL}/api/compose-hardcode-video/${sessionId}`,
        {
          method: "POST",
          headers: {
            "X-User-Email": userEmail,
          },
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail ||
            `Video composition failed: ${response.statusText}`,
        );
      }

      const result = await response.json();
      console.log("[HardcodeCreate] Video composition started:", result);
      setProgress("Composing video from images and audio...");
    } catch (err) {
      console.error("[HardcodeCreate] Error starting video composition:", err);
      setIsLoading(false);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to start video composition",
      );
      setProgress(null);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Session Information</CardTitle>
          <CardDescription className="space-y-2">
            <div>
              Session ID:{" "}
              <code className="bg-muted rounded px-2 py-1 text-xs">
                {sessionId}
              </code>
            </div>
            {activeSessionId && (
              <div className="flex items-center gap-2 text-xs">
                <div
                  className={`h-2 w-2 rounded-full ${isConnected ? "bg-green-500" : "bg-gray-400"}`}
                />
                <span>
                  WebSocket: {isConnected ? "Connected" : "Disconnected"}
                </span>
              </div>
            )}
          </CardDescription>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Template Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="template-title">Template Title</Label>
            <Input
              id="template-title"
              value={templateTitle}
              onChange={(e) => setTemplateTitle(e.target.value)}
              placeholder="Photosynthesis"
              required
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Story Segments</CardTitle>
          <CardDescription>
            Enter the narration text and visual guidance for each segment
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Hook */}
          <div className="space-y-4">
            <h3 className="font-semibold">Segment 1: Hook (0-10 seconds)</h3>
            <div className="space-y-2">
              <Label htmlFor="hook-text">Narration Text</Label>
              <Textarea
                id="hook-text"
                value={hookText}
                onChange={(e) => setHookText(e.target.value)}
                rows={4}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="hook-visual">Visual Guidance Preview</Label>
              <Input
                id="hook-visual"
                value={hookVisualGuidance}
                onChange={(e) => setHookVisualGuidance(e.target.value)}
                placeholder="Animated question mark with plant growing time-lapse"
                required
              />
            </div>
          </div>

          {/* Concept */}
          <div className="space-y-4">
            <h3 className="font-semibold">
              Segment 2: Concept Introduction (10-25 seconds)
            </h3>
            <div className="space-y-2">
              <Label htmlFor="concept-text">Narration Text</Label>
              <Textarea
                id="concept-text"
                value={conceptText}
                onChange={(e) => setConceptText(e.target.value)}
                rows={4}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="concept-visual">Visual Guidance Preview</Label>
              <Input
                id="concept-visual"
                value={conceptVisualGuidance}
                onChange={(e) => setConceptVisualGuidance(e.target.value)}
                placeholder="Diagram of leaf → zoom to chloroplast → highlight chlorophyll"
                required
              />
            </div>
          </div>

          {/* Process */}
          <div className="space-y-4">
            <h3 className="font-semibold">
              Segment 3: Process Explanation (25-45 seconds)
            </h3>
            <div className="space-y-2">
              <Label htmlFor="process-text">Narration Text</Label>
              <Textarea
                id="process-text"
                value={processText}
                onChange={(e) => setProcessText(e.target.value)}
                rows={4}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="process-visual">Visual Guidance Preview</Label>
              <Input
                id="process-visual"
                value={processVisualGuidance}
                onChange={(e) => setProcessVisualGuidance(e.target.value)}
                placeholder="Animated diagram showing CO₂ + H₂O → glucose + O₂ with arrows"
                required
              />
            </div>
          </div>

          {/* Conclusion */}
          <div className="space-y-4">
            <h3 className="font-semibold">
              Segment 4: Conclusion (45-60 seconds)
            </h3>
            <div className="space-y-2">
              <Label htmlFor="conclusion-text">Narration Text</Label>
              <Textarea
                id="conclusion-text"
                value={conclusionText}
                onChange={(e) => setConclusionText(e.target.value)}
                rows={4}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="conclusion-visual">Visual Guidance Preview</Label>
              <Input
                id="conclusion-visual"
                value={conclusionVisualGuidance}
                onChange={(e) => setConclusionVisualGuidance(e.target.value)}
                placeholder="Real-world footage of child near tree, text overlay with key takeaway"
                required
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Diagram Upload (Optional)</CardTitle>
          <CardDescription>
            Upload a reference diagram to guide image generation style
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="diagram-file">Diagram Image</Label>
            <Input
              id="diagram-file"
              type="file"
              accept="image/*"
              ref={fileInputRef}
              onChange={handleFileChange}
            />
            {diagramFile && (
              <p className="text-muted-foreground text-sm">
                Selected: {diagramFile.name}
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <Collapsible open={isAdvancedOpen} onOpenChange={setIsAdvancedOpen}>
        <Card>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer">
              <div className="flex items-center justify-between">
                <CardTitle>Advanced Options</CardTitle>
                {isAdvancedOpen ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </div>
            </CardHeader>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="num-images">Number of Images per Segment</Label>
                <Input
                  id="num-images"
                  type="number"
                  min={1}
                  max={3}
                  value={numImages}
                  onChange={(e) => {
                    const val = parseInt(e.target.value) || 2;
                    setNumImages(Math.min(Math.max(val, 1), 3));
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max-passes">Max Passes</Label>
                <Input
                  id="max-passes"
                  type="number"
                  min="1"
                  max="10"
                  value={maxPasses}
                  onChange={(e) => setMaxPasses(parseInt(e.target.value) || 5)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max-verification-passes">
                  Max Verification Passes
                </Label>
                <Input
                  id="max-verification-passes"
                  type="number"
                  min="1"
                  max="5"
                  value={maxVerificationPasses}
                  onChange={(e) =>
                    setMaxVerificationPasses(parseInt(e.target.value) || 3)
                  }
                />
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="fast-mode"
                  checked={fastMode}
                  onChange={(e) => setFastMode(e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300"
                />
                <Label htmlFor="fast-mode" className="cursor-pointer">
                  Fast Mode
                </Label>
              </div>
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {success && (
        <Card className="border-green-500">
          <CardContent className="pt-6">
            <div className="mb-6 flex items-center justify-between">
              <p className="font-medium text-green-600">
                Success! Images and audio have been generated.
              </p>
              <Button
                onClick={handleComposeVideo}
                disabled={isLoading}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {isLoading ? "Composing..." : "Compose Video"}
              </Button>
            </div>

            {/* Display generated assets from WebSocket */}
            {(generatedImages.length > 0 || generatedAudio.length > 0) && (
              <div className="mt-6 space-y-6">
                <div className="text-muted-foreground flex items-center justify-between border-b pb-3 text-sm">
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Total Images:</span>{" "}
                    {generatedImages.length}
                  </span>
                  {totalCost !== null && (
                    <span className="flex items-center gap-1">
                      <span className="font-medium">Cost:</span> $
                      {totalCost.toFixed(4)}
                    </span>
                  )}
                  {elapsedTime !== null && (
                    <span className="flex items-center gap-1">
                      <span className="font-medium">Time:</span>{" "}
                      {elapsedTime.toFixed(1)}s
                    </span>
                  )}
                </div>

                {/* Display audio files */}
                {generatedAudio.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Generated Audio</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {generatedAudio.map((audio: any, idx: number) => (
                        <div key={idx} className="rounded border p-3">
                          <Label className="mb-2 block text-sm font-medium capitalize">
                            {audio.part}{" "}
                            {audio.duration &&
                              `(${audio.duration.toFixed(1)}s)`}
                          </Label>
                          <audio controls className="w-full">
                            <source src={audio.url} type="audio/mpeg" />
                            Your browser does not support the audio element.
                          </audio>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}

                {/* Display images */}
                {generatedImages.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">
                        Generated Images
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
                        {generatedImages.map((image: any, idx: number) => (
                          <div key={idx} className="relative">
                            <img
                              src={image.url}
                              alt={`${image.segment_title}`}
                              className="h-auto w-full rounded border"
                            />
                            <span className="absolute bottom-2 left-2 rounded bg-black/70 px-2 py-1 text-xs text-white">
                              {image.segment_title}
                            </span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {results && (
              <div className="mt-6 space-y-6">
                <div className="text-muted-foreground flex items-center justify-between border-b pb-3 text-sm">
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Total Images:</span>{" "}
                    {results.total_images_generated}
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Cost:</span> $
                    {results.total_cost_usd?.toFixed(4)}
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Time:</span>{" "}
                    {results.total_time_seconds?.toFixed(1)}s
                  </span>
                </div>

                {/* Display segments with images and audio */}
                {results.segments &&
                  results.segments.map((segment: any) => (
                    <Card key={segment.segment_number}>
                      <CardHeader>
                        <CardTitle className="text-lg">
                          Segment {segment.segment_number}:{" "}
                          {segment.segment_title}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* Audio player if available */}
                        {segment.audio_url && (
                          <div>
                            <Label className="mb-2 block text-sm font-medium">
                              Audio
                            </Label>
                            <audio controls className="w-full">
                              <source
                                src={segment.audio_url}
                                type="audio/mpeg"
                              />
                              Your browser does not support the audio element.
                            </audio>
                          </div>
                        )}

                        {/* Images */}
                        {segment.images && segment.images.length > 0 && (
                          <div>
                            <Label className="mb-2 block text-sm font-medium">
                              Images ({segment.images.length})
                            </Label>
                            <div className="grid grid-cols-2 gap-4">
                              {segment.images.map((image: any) => (
                                <div key={image.s3_key} className="relative">
                                  <img
                                    src={image.presigned_url}
                                    alt={`Image ${image.image_number}`}
                                    className="h-auto w-full rounded border"
                                  />
                                  <span className="absolute top-2 left-2 rounded bg-black/70 px-2 py-1 text-xs text-white">
                                    #{image.image_number}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {progress && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                <p className="text-sm font-medium">{progress}</p>
              </div>

              {/* Show generated assets WHILE processing */}
              {(generatedImages.length > 0 || generatedAudio.length > 0) && (
                <div className="mt-4 space-y-4 border-t pt-4">
                  {/* Display audio files as they become available */}
                  {generatedAudio.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-medium">
                        Generated Audio ({generatedAudio.length})
                      </Label>
                      <div className="space-y-2">
                        {generatedAudio.map((audio: any, idx: number) => (
                          <div
                            key={`${audio.part}-${idx}`}
                            className="rounded border bg-white p-2"
                          >
                            <Label className="mb-1 block text-xs font-medium capitalize">
                              {audio.part}{" "}
                              {audio.duration &&
                                `(${audio.duration.toFixed(1)}s)`}
                            </Label>
                            <audio controls className="h-8 w-full">
                              <source src={audio.url} type="audio/mpeg" />
                            </audio>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Display images as they become available */}
                  {generatedImages.length > 0 && (
                    <div className="space-y-2">
                      <Label className="text-sm font-medium">
                        Generated Images ({generatedImages.length})
                      </Label>
                      <div className="grid grid-cols-3 gap-2 md:grid-cols-4">
                        {generatedImages.map((image: any, idx: number) => (
                          <div key={`${image.url}-${idx}`} className="relative">
                            <img
                              src={image.url}
                              alt={image.segment_title}
                              className="h-auto w-full rounded border bg-white"
                            />
                            <span className="absolute bottom-1 left-1 rounded bg-black/70 px-1 py-0.5 text-xs text-white">
                              {image.segment_title}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Cumulative status items */}
              {statusItems && statusItems.length > 0 && (
                <div className="space-y-2 border-t pt-3">
                  <p className="text-muted-foreground mb-2 text-xs font-medium">
                    Progress Details:
                  </p>
                  <div className="max-h-48 space-y-1 overflow-y-auto">
                    {statusItems.map((item: any) => (
                      <div
                        key={item.id}
                        className="flex items-center gap-2 text-xs"
                      >
                        {item.status === "completed" && (
                          <svg
                            className="h-4 w-4 flex-shrink-0 text-green-600"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        )}
                        {item.status === "processing" && (
                          <Loader2 className="h-4 w-4 flex-shrink-0 animate-spin text-blue-600" />
                        )}
                        {item.status === "pending" && (
                          <svg
                            className="h-4 w-4 flex-shrink-0 text-gray-400"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <circle cx="12" cy="12" r="10" strokeWidth={2} />
                          </svg>
                        )}
                        <span
                          className={
                            item.status === "completed"
                              ? "text-green-700"
                              : item.status === "processing"
                                ? "font-medium text-blue-700"
                                : "text-gray-500"
                          }
                        >
                          {item.name}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Live stats */}
              <div className="text-muted-foreground flex items-center justify-between border-t pt-3 text-sm">
                {elapsedTime !== null && (
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Time:</span>{" "}
                    {elapsedTime.toFixed(1)}s
                  </span>
                )}
                {totalCost !== null && (
                  <span className="flex items-center gap-1">
                    <span className="font-medium">Cost:</span> $
                    {totalCost.toFixed(4)}
                  </span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Button type="submit" disabled={isLoading} className="w-full">
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Processing...
          </>
        ) : (
          "Save and Generate Images"
        )}
      </Button>
    </form>
  );
}
