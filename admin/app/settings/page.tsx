"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input, Select } from "../components/ui/input";

interface Config {
  chunk_size: number;
  chunk_overlap: number;
  model: string;
  embedding_model: string;
  temperature: number;
  max_tokens: number;
  theme: string;
  language: string;
}

const DEFAULT_CONFIG: Config = {
  chunk_size: 512,
  chunk_overlap: 64,
  model: "gpt-4o-mini",
  embedding_model: "text-embedding-3-small",
  temperature: 0.3,
  max_tokens: 1024,
  theme: "dark",
  language: "en",
};

const modelOptions = [
  { value: "gpt-4o-mini", label: "GPT-4o Mini" },
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
  { value: "claude-3-haiku", label: "Claude 3 Haiku" },
  { value: "claude-3-sonnet", label: "Claude 3 Sonnet" },
];

const embeddingOptions = [
  { value: "text-embedding-3-small", label: "text-embedding-3-small" },
  { value: "text-embedding-3-large", label: "text-embedding-3-large" },
  { value: "text-embedding-ada-002", label: "text-embedding-ada-002" },
];

const themeOptions = [
  { value: "dark", label: "Dark" },
  { value: "light", label: "Light" },
  { value: "system", label: "System" },
];

const languageOptions = [
  { value: "en", label: "English" },
  { value: "ru", label: "Русский" },
  { value: "es", label: "Español" },
  { value: "de", label: "Deutsch" },
];

export default function SettingsPage() {
  const [config, setConfig] = useState<Config>(DEFAULT_CONFIG);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  function updateConfig<K extends keyof Config>(key: K, value: Config[K]) {
    setConfig((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    // Mock save — in production this would PUT to /api/config
    await new Promise((r) => setTimeout(r, 500));
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-slate-400 mt-1">Configure RAG widget behavior</p>
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        {/* Chunking */}
        <Card>
          <CardHeader>
            <CardTitle>Chunking</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Chunk Size (tokens)"
                type="number"
                min={64}
                max={2048}
                value={config.chunk_size}
                onChange={(e) =>
                  updateConfig("chunk_size", parseInt(e.target.value) || 512)
                }
              />
              <Input
                label="Chunk Overlap (tokens)"
                type="number"
                min={0}
                max={512}
                value={config.chunk_overlap}
                onChange={(e) =>
                  updateConfig("chunk_overlap", parseInt(e.target.value) || 0)
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Models */}
        <Card>
          <CardHeader>
            <CardTitle>Models</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Chat Model"
                options={modelOptions}
                value={config.model}
                onChange={(e) => updateConfig("model", e.target.value)}
              />
              <Select
                label="Embedding Model"
                options={embeddingOptions}
                value={config.embedding_model}
                onChange={(e) => updateConfig("embedding_model", e.target.value)}
              />
              <Input
                label="Temperature"
                type="number"
                min={0}
                max={2}
                step={0.1}
                value={config.temperature}
                onChange={(e) =>
                  updateConfig("temperature", parseFloat(e.target.value) || 0)
                }
              />
              <Input
                label="Max Tokens"
                type="number"
                min={64}
                max={4096}
                value={config.max_tokens}
                onChange={(e) =>
                  updateConfig("max_tokens", parseInt(e.target.value) || 1024)
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle>Appearance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Theme"
                options={themeOptions}
                value={config.theme}
                onChange={(e) => updateConfig("theme", e.target.value)}
              />
              <Select
                label="Language"
                options={languageOptions}
                value={config.language}
                onChange={(e) => updateConfig("language", e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Save */}
        <div className="flex items-center gap-4">
          <Button type="submit" size="lg" disabled={saving}>
            {saving ? "Saving..." : "Save Settings"}
          </Button>
          {saved && (
            <span className="text-sm text-emerald-400 font-medium">
              ✓ Settings saved
            </span>
          )}
        </div>
      </form>
    </div>
  );
}
