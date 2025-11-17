"use client";

import { useState, useRef } from "react";
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

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

interface HardcodeCreateFormProps {
  userEmail: string;
}

export function HardcodeCreateForm({ userEmail }: HardcodeCreateFormProps) {
  const [templateTitle, setTemplateTitle] = useState("Photosynthesis");
  const [hookText, setHookText] = useState(
    'Have you ever wondered how plants make their own food? Let\'s discover the amazing process of photosynthesis!'
  );
  const [conceptText, setConceptText] = useState(
    "Plants use a process called photosynthesis. Inside their leaves are tiny structures called chloroplasts that contain chlorophyll - the green pigment that captures sunlight."
  );
  const [processText, setProcessText] = useState(
    "When sunlight hits the chlorophyll, it triggers a chemical reaction. The plant takes in carbon dioxide from the air and water from the soil, and converts them into glucose - that's sugar, the plant's food! The chemical equation is: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂"
  );
  const [conclusionText, setConclusionText] = useState(
    "As a bonus, plants release oxygen as a byproduct. That's the air we breathe! So next time you see a green plant, remember - it's a tiny food factory powered by the sun."
  );
  const [hookVisualGuidance, setHookVisualGuidance] = useState(
    "Animated question mark with plant growing time-lapse"
  );
  const [conceptVisualGuidance, setConceptVisualGuidance] = useState(
    "Diagram of leaf → zoom to chloroplast → highlight chlorophyll"
  );
  const [processVisualGuidance, setProcessVisualGuidance] = useState(
    "Animated diagram showing CO₂ + H₂O → glucose + O₂ with arrows"
  );
  const [conclusionVisualGuidance, setConclusionVisualGuidance] = useState(
    "Real-world footage of child near tree, text overlay with key takeaway"
  );
  const [diagramFile, setDiagramFile] = useState<File | null>(null);
  const [sessionId, setSessionId] = useState<string>(() => {
    // Generate UUID v4
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  });
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [numImages, setNumImages] = useState(2);
  const [maxPasses, setMaxPasses] = useState(5);
  const [maxVerificationPasses, setMaxVerificationPasses] = useState(3);
  const [fastMode, setFastMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

    try {
      // User email is passed as prop from server component

      // Generate segments.md content
      const segmentsMdContent = generateSegmentsMd();

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
      formData.append("segments_md", new Blob([segmentsMdContent], { type: "text/markdown" }), "segments.md");
      if (diagramFile) {
        formData.append("diagram", diagramFile);
      }
      formData.append("num_images", numImages.toString());
      formData.append("max_passes", maxPasses.toString());
      formData.append("max_verification_passes", maxVerificationPasses.toString());
      formData.append("fast_mode", fastMode.toString());

      setProgress("Uploading files to S3...");

      // Upload files and trigger processing
      const response = await fetch(`${API_URL}/api/hardcode-upload`, {
        method: "POST",
        headers: {
          "X-User-Email": userEmail,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      setProgress("Processing started! Generating images...");

      // Poll for completion
      let pollAttempts = 0;
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await fetch(
            `${API_URL}/api/story-images/${sessionId}`,
            {
              headers: {
                "X-User-Email": userEmail,
              },
            }
          );

          if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            if (statusData.status === "completed" || statusData.status === "partial_failure") {
              clearInterval(pollInterval);
              setIsLoading(false);
              setSuccess(true);
              setProgress(null);
            } else if (statusData.status === "failed") {
              clearInterval(pollInterval);
              setIsLoading(false);
              setError("Image generation failed");
              setProgress(null);
            } else {
              setProgress(`Processing... ${statusData.segments_succeeded || 0}/${statusData.segments_total || 4} segments completed`);
            }
          } else if (statusResponse.status === 404) {
            // Status file not created yet - this is normal in the first few seconds
            pollAttempts++;
            if (pollAttempts <= 5) {
              // First 5 attempts (15 seconds) - status file might not exist yet
              setProgress("Initializing processing...");
            } else {
              // After 15 seconds, if still 404, there might be an issue
              // But continue polling in case it's just slow
            }
          }
        } catch (err) {
          // Continue polling on error (network errors, etc.)
          pollAttempts++;
          if (pollAttempts > 10) {
            // After 30 seconds of errors, log but continue
            console.warn("Polling error (continuing):", err);
          }
        }
      }, 3000); // Poll every 3 seconds

      // Stop polling after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        if (isLoading) {
          setIsLoading(false);
          setProgress("Processing is taking longer than expected. Check the Assets page for results.");
        }
      }, 300000);
    } catch (err) {
      setIsLoading(false);
      setError(err instanceof Error ? err.message : "An error occurred");
      setProgress(null);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Session Information</CardTitle>
          <CardDescription>
            Session ID: <code className="text-xs bg-muted px-2 py-1 rounded">{sessionId}</code>
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
            <h3 className="font-semibold">Segment 2: Concept Introduction (10-25 seconds)</h3>
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
            <h3 className="font-semibold">Segment 3: Process Explanation (25-45 seconds)</h3>
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
            <h3 className="font-semibold">Segment 4: Conclusion (45-60 seconds)</h3>
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
              <p className="text-sm text-muted-foreground">
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
                <Label htmlFor="max-verification-passes">Max Verification Passes</Label>
                <Input
                  id="max-verification-passes"
                  type="number"
                  min="1"
                  max="5"
                  value={maxVerificationPasses}
                  onChange={(e) => setMaxVerificationPasses(parseInt(e.target.value) || 3)}
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
            <p className="text-green-600">
              Success! Images are being generated. Check the Assets page to view results.
            </p>
          </CardContent>
        </Card>
      )}

      {progress && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin" />
              <p className="text-muted-foreground">{progress}</p>
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

