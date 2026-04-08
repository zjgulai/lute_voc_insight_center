"use client";

import { useEffect, useState } from "react";
import { api } from "../../lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface TableInfo {
  filename: string;
  exists: boolean;
  rows: number;
  size_bytes: number;
  modified_at: string | null;
  dashboards: string[];
}

interface JsonInfo {
  filename: string;
  exists: boolean;
  size_bytes: number;
  modified_at: string | null;
}

interface AdminStatus {
  tables: TableInfo[];
  json_outputs: JsonInfo[];
}

interface TaskResult {
  success: boolean;
  exit_code: number;
  stdout: string;
  stderr: string;
}

async function adminPost<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST" });
  return res.json() as Promise<T>;
}

async function adminGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  return res.json() as Promise<T>;
}

function DashboardBadge({ name }: { name: string }) {
  const colors: Record<string, string> = {
    country_insight: "var(--color-info-bg)",
    opportunity: "var(--color-warning-bg, #fef3c7)",
  };
  const labels: Record<string, string> = {
    country_insight: "国家洞察",
    opportunity: "机会点识别",
  };
  return (
    <span
      style={{
        display: "inline-block",
        fontSize: 10,
        padding: "1px 6px",
        borderRadius: "var(--radius-sm)",
        background: colors[name] || "var(--color-bg-card-alt)",
        border: "1px solid var(--color-border)",
        marginRight: 4,
      }}
    >
      {labels[name] || name}
    </span>
  );
}

const IS_STATIC = process.env.NEXT_PUBLIC_STATIC_MODE === "true";

export default function AdminPage() {
  if (IS_STATIC) {
    return (
      <>
        <div className="page-header">
          <h1 className="page-title">数据运维台</h1>
          <p className="page-desc">数据源状态、ETL 编排、校验与预览</p>
        </div>
        <div className="card" style={{ textAlign: "center", padding: "var(--space-2xl)" }}>
          <div style={{ fontSize: 48, marginBottom: "var(--space-md)", opacity: 0.3 }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
          </div>
          <div className="card-title" style={{ justifyContent: "center" }}>运营后台仅本地可用</div>
          <p style={{ fontSize: 13, color: "var(--color-text-secondary)", maxWidth: 400, margin: "0 auto" }}>
            数据采集、ETL 导出、校验和预览功能需要本地 Python 后端。
            请参阅项目 README 在本地启动完整后端后访问此页面。
          </p>
        </div>
      </>
    );
  }

  const [health, setHealth] = useState<{ status: string; version?: string } | null>(null);
  const [status, setStatus] = useState<AdminStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [taskMsg, setTaskMsg] = useState<string | null>(null);
  const [taskRunning, setTaskRunning] = useState(false);

  async function loadStatus() {
    try {
      const [h, s] = await Promise.all([
        api.health(),
        adminGet<AdminStatus>("/api/v1/admin/status"),
      ]);
      setHealth(h as { status: string; version?: string });
      setStatus(s);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => { loadStatus(); }, []);

  async function runTask(label: string, path: string) {
    setTaskRunning(true);
    setTaskMsg(`${label} 执行中...`);
    try {
      const result = await adminPost<TaskResult>(path);
      setTaskMsg(
        result.success
          ? `${label} 完成\n${result.stdout.slice(-500)}`
          : `${label} 失败 (exit ${result.exit_code})\n${result.stderr.slice(-500)}`
      );
      await loadStatus();
    } catch (e) {
      setTaskMsg(`${label} 异常: ${(e as Error).message}`);
    } finally {
      setTaskRunning(false);
    }
  }

  const countryTables = status?.tables.filter((t) => t.dashboards.includes("country_insight")) || [];
  const oppTables = status?.tables.filter((t) => t.dashboards.includes("opportunity")) || [];

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">数据运维台</h1>
        <p className="page-desc">数据源状态、ETL 编排、校验与预览</p>
      </div>

      <div className="dual-grid">
        <div className="card">
          <div className="card-title">系统健康</div>
          {error ? (
            <div className="alert-error">后端连接失败: {error}</div>
          ) : health ? (
            <div className="stat-grid">
              <div className="stat-card">
                <div className="stat-value" style={{ color: health.status === "ok" ? "var(--color-success)" : "var(--color-error)" }}>
                  {health.status === "ok" ? "正常" : "异常"}
                </div>
                <div className="stat-label">API 状态</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{health.version || "—"}</div>
                <div className="stat-label">API 版本</div>
              </div>
            </div>
          ) : (
            <div className="loading-text">检测中...</div>
          )}
        </div>

        <div className="card">
          <div className="card-title">JSON 产物状态</div>
          {status?.json_outputs ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>文件</th><th>大小</th><th>更新时间</th></tr>
                </thead>
                <tbody>
                  {status.json_outputs.map((j) => (
                    <tr key={j.filename}>
                      <td style={{ fontSize: 12, fontFamily: "var(--font-mono, monospace)" }}>{j.filename}</td>
                      <td style={{ fontSize: 12 }}>{j.exists ? `${(j.size_bytes / 1024).toFixed(0)} KB` : "不存在"}</td>
                      <td style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>{j.modified_at?.slice(0, 19) || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="loading-text">加载中...</div>
          )}
        </div>
      </div>

      <div className="dual-grid" style={{ marginTop: "var(--space-md)" }}>
        <div className="card">
          <div className="card-title">国家洞察数据源</div>
          {countryTables.length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>文件</th><th>行数</th><th>更新时间</th></tr>
                </thead>
                <tbody>
                  {countryTables.map((t) => (
                    <tr key={t.filename}>
                      <td style={{ fontSize: 12, fontFamily: "var(--font-mono, monospace)" }}>
                        {t.filename}
                        {t.dashboards.length > 1 && t.dashboards.map((d) => <DashboardBadge key={d} name={d} />)}
                      </td>
                      <td style={{ fontSize: 12 }}>{t.exists ? t.rows : "缺失"}</td>
                      <td style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>{t.modified_at?.slice(0, 19) || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="loading-text">加载中...</div>
          )}
        </div>

        <div className="card">
          <div className="card-title">机会点识别数据源</div>
          {oppTables.length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr><th>文件</th><th>行数</th><th>更新时间</th></tr>
                </thead>
                <tbody>
                  {oppTables.map((t) => (
                    <tr key={t.filename}>
                      <td style={{ fontSize: 12, fontFamily: "var(--font-mono, monospace)" }}>
                        {t.filename}
                      </td>
                      <td style={{ fontSize: 12 }}>{t.exists ? t.rows : "缺失"}</td>
                      <td style={{ fontSize: 11, color: "var(--color-text-secondary)" }}>{t.modified_at?.slice(0, 19) || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="loading-text">加载中...</div>
          )}
        </div>
      </div>

      <div className="card" style={{ marginTop: "var(--space-md)" }}>
        <div className="card-title">数据操作</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-sm)" }}>
          <button className="btn-primary" onClick={() => runTask("竞品 ZIP 导入", "/api/v1/admin/ingest-competitor-zip")} type="button" disabled={taskRunning}>
            竞品 ZIP 导入
          </button>
          <button className="btn-primary" onClick={() => runTask("数据导出", "/api/v1/admin/export")} type="button" disabled={taskRunning}>
            重新导出 JSON
          </button>
          <button className="btn-primary" onClick={() => runTask("数据校验", "/api/v1/admin/validate")} type="button" disabled={taskRunning}>
            运行校验
          </button>
          <button className="btn-primary" onClick={() => runTask("缓存刷新", "/api/v1/admin/reload")} type="button" disabled={taskRunning}>
            Reload 缓存
          </button>
        </div>
        {taskMsg && (
          <pre style={{
            marginTop: "var(--space-sm)",
            padding: "var(--space-sm)",
            background: "var(--color-bg-card-alt)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-sm)",
            fontSize: 12,
            maxHeight: 300,
            overflow: "auto",
            whiteSpace: "pre-wrap",
          }}>
            {taskMsg}
          </pre>
        )}
      </div>
    </>
  );
}
