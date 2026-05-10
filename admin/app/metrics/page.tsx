"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

interface MetricsData {
  totalQueries: number;
  avgLatencyMs: number;
  cacheHitRate: number;
  totalTokens: number;
  activeUsers: number;
  errorRate: number;
  dailyQueries: { day: string; count: number }[];
  topSources: { source: string; queries: number }[];
}

const MOCK_METRICS: MetricsData = {
  totalQueries: 1247,
  avgLatencyMs: 342,
  cacheHitRate: 68.5,
  totalTokens: 89420,
  activeUsers: 23,
  errorRate: 2.1,
  dailyQueries: [
    { day: "Mon", count: 145 },
    { day: "Tue", count: 189 },
    { day: "Wed", count: 201 },
    { day: "Thu", count: 178 },
    { day: "Fri", count: 220 },
    { day: "Sat", count: 156 },
    { day: "Sun", count: 158 },
  ],
  topSources: [
    { source: "product-guide.pdf", queries: 312 },
    { source: "faq.txt", queries: 198 },
    { source: "api-docs.md", queries: 145 },
    { source: "changelog.md", queries: 87 },
  ],
};

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // In MOCK_MODE, use mock data directly
    setTimeout(() => {
      setMetrics(MOCK_METRICS);
      setLoading(false);
    }, 300);
  }, []);

  if (loading || !metrics) {
    return (
      <div className="space-y-8">
        <h1 className="text-3xl font-bold">Metrics</h1>
        <p className="text-slate-400">Loading metrics...</p>
      </div>
    );
  }

  const maxDaily = Math.max(...metrics.dailyQueries.map((d) => d.count));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Metrics</h1>
        <p className="text-slate-400 mt-1">Performance and usage analytics</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-slate-400 text-sm font-medium">
              Total Queries
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {metrics.totalQueries.toLocaleString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-slate-400 text-sm font-medium">
              Avg Latency
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{metrics.avgLatencyMs}ms</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-slate-400 text-sm font-medium">
              Cache Hit Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{metrics.cacheHitRate}%</p>
            <div className="mt-2 h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 rounded-full"
                style={{ width: `${metrics.cacheHitRate}%` }}
              />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-slate-400 text-sm font-medium">
              Total Tokens Used
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {metrics.totalTokens.toLocaleString()}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-slate-400 text-sm font-medium">
              Active Users
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{metrics.activeUsers}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-slate-400 text-sm font-medium">
              Error Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{metrics.errorRate}%</p>
          </CardContent>
        </Card>
      </div>

      {/* Weekly query chart (simple bar chart) */}
      <Card>
        <CardHeader>
          <CardTitle>Queries This Week</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-3 h-40">
            {metrics.dailyQueries.map((d) => (
              <div key={d.day} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-xs text-slate-400">{d.count}</span>
                <div
                  className="w-full bg-blue-500 rounded-t-md transition-all"
                  style={{ height: `${(d.count / maxDaily) * 100}%` }}
                />
                <span className="text-xs text-slate-400">{d.day}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Top sources */}
      <Card>
        <CardHeader>
          <CardTitle>Top Sources by Query Count</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {metrics.topSources.map((s, i) => (
              <div key={s.source} className="flex items-center gap-3">
                <span className="text-sm text-slate-400 w-5 text-right">
                  {i + 1}.
                </span>
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-sm font-medium">{s.source}</span>
                    <span className="text-sm text-slate-400">
                      {s.queries} queries
                    </span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{
                        width: `${(s.queries / metrics.topSources[0].queries) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
