"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Input } from "../components/ui/input";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type DocStatus = "indexed" | "embedding" | "failed";

interface Document {
  id: string;
  name: string;
  type: string;
  chunks: number;
  status: DocStatus;
  uploadedAt: string;
}

const MOCK_DOCUMENTS: Document[] = [
  { id: "1", name: "product-guide.pdf", type: "PDF", chunks: 48, status: "indexed", uploadedAt: "2025-05-10" },
  { id: "2", name: "faq.txt", type: "TXT", chunks: 22, status: "indexed", uploadedAt: "2025-05-11" },
  { id: "3", name: "api-docs.md", type: "MD", chunks: 35, status: "embedding", uploadedAt: "2025-05-14" },
  { id: "4", name: "legacy-notes.docx", type: "DOCX", chunks: 0, status: "failed", uploadedAt: "2025-05-15" },
];

const statusVariant: Record<DocStatus, "success" | "warning" | "destructive"> = {
  indexed: "success",
  embedding: "warning",
  failed: "destructive",
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/health`);
      if (!res.ok) throw new Error("offline");
      // Backend doesn't expose document list yet — use mock data
      setDocuments(MOCK_DOCUMENTS);
    } catch {
      setDocuments(MOCK_DOCUMENTS);
    } finally {
      setLoading(false);
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
      const newDoc: Document = {
        id: String(Date.now()),
        name: file.name,
        type: file.name.split(".").pop()?.toUpperCase() || "FILE",
        chunks: 0,
        status: "embedding",
        uploadedAt: new Date().toISOString().slice(0, 10),
      };
      setDocuments((prev) => [newDoc, ...prev]);
      setFile(null);
    } catch (err) {
      alert(String(err));
    } finally {
      setUploading(false);
    }
  }

  const filtered = documents.filter((d) =>
    d.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Documents</h1>
        <p className="text-slate-400 mt-1">Manage indexed documents</p>
      </div>

      {/* Upload form */}
      <Card>
        <CardHeader>
          <CardTitle>Upload New Document</CardTitle>
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

      {/* Search */}
      <Input
        placeholder="Search documents..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {/* Document list */}
      <Card>
        <CardHeader>
          <CardTitle>All Documents ({filtered.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-slate-400">Loading...</p>
          ) : filtered.length === 0 ? (
            <p className="text-slate-400">No documents found.</p>
          ) : (
            <div className="space-y-2">
              {filtered.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between bg-slate-700/50 rounded-lg px-4 py-3 hover:bg-slate-700 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="text-xl">📄</span>
                    <div className="min-w-0">
                      <p className="font-medium truncate">{doc.name}</p>
                      <p className="text-xs text-slate-400">
                        {doc.type} · {doc.chunks} chunks · {doc.uploadedAt}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={statusVariant[doc.status]}>
                      {doc.status}
                    </Badge>
                    <Button variant="ghost" size="sm">
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
