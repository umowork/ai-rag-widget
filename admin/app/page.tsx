"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Button } from "./components/ui/button";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Document {
  id: string;
  source: string;
  chunks: number;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [embedCode, setEmbedCode] = useState("");

  useEffect(() => {
    fetchDocuments();
    setEmbedCode(
      `<script src="${API_URL}/widget.js"></script>\n<script>window.AI_RAG_API_URL = "${API_URL}";</script>`
    );
  }, []);

  async function fetchDocuments() {
    setLoadingDocs(true);
    try {
      const res = await fetch(`${API_URL}/health`);
      if (!res.ok) throw new Error("API unavailable");
      setDocuments([{ id: "1", source: "example.pdf", chunks: 12 }]);
    } catch {
      setDocuments([]);
    } finally {
      setLoadingDocs(false);
    }
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${API_URL}/upload/file`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error("Upload failed");
      setFile(null);
      await fetchDocuments();
    } catch (err) {
      alert(String(err));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-slate-400 mt-1">Overview of your RAG widget</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-slate-400 text-sm font-medium">
              Total Documents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{documents.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-slate-400 text-sm font-medium">
              Total Chunks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {documents.reduce((sum, d) => sum + d.chunks, 0)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-slate-400 text-sm font-medium">
              API Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <span className="inline-flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-sm font-medium text-emerald-400">Online</span>
            </span>
          </CardContent>
        </Card>
      </div>

      {/* Upload */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Document</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUpload} className="flex items-center gap-4">
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500"
            />
            <Button type="submit" disabled={!file || uploading}>
              {uploading ? "Uploading..." : "Upload"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Documents */}
      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingDocs ? (
            <p className="text-slate-400">Loading...</p>
          ) : documents.length === 0 ? (
            <p className="text-slate-400">No documents uploaded yet.</p>
          ) : (
            <ul className="space-y-2">
              {documents.map((doc) => (
                <li
                  key={doc.id}
                  className="flex justify-between items-center bg-slate-700 rounded-lg px-4 py-3"
                >
                  <span className="font-medium">{doc.source}</span>
                  <span className="text-sm text-slate-400">
                    {doc.chunks} chunks
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Embed code */}
      <Card>
        <CardHeader>
          <CardTitle>Embed Code</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-slate-400 mb-2">
            Paste this into your website HTML:
          </p>
          <pre className="bg-slate-900 rounded-lg p-4 text-sm overflow-x-auto border border-slate-700">
            <code>{embedCode}</code>
          </pre>
          <Button
            variant="success"
            className="mt-3"
            onClick={() => navigator.clipboard.writeText(embedCode)}
          >
            Copy to Clipboard
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
