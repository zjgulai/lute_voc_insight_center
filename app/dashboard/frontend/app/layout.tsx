"use client";

import "./globals.css";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "概览" },
  { href: "/countries", label: "国家画像" },
  { href: "/viz", label: "国家洞察" },
  { href: "/opportunities", label: "机会点识别" },
  { href: "/admin", label: "运营后台" },
];

function NavBar({
  theme,
  onToggleTheme,
}: {
  theme: "light" | "dark";
  onToggleTheme: () => void;
}) {
  const pathname = usePathname();

  function isActive(href: string) {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  }

  return (
    <nav className="nav" role="navigation" aria-label="主导航">
      <div className="nav-inner">
        <a href="/" className="nav-brand">
          <span className="nav-brand-icon">L</span>
          路特外部社媒聆听洞察中台
        </a>
        <div className="nav-links">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="nav-link"
              data-active={isActive(item.href)}
              aria-current={isActive(item.href) ? "page" : undefined}
            >
              {item.label}
            </a>
          ))}
          <button
            className="nav-theme-toggle"
            onClick={onToggleTheme}
            type="button"
            aria-label={theme === "dark" ? "切换到浅色模式" : "切换到深色模式"}
          >
            {theme === "dark" ? "☀ 浅色" : "☽ 深色"}
          </button>
        </div>
      </div>
    </nav>
  );
}

export default function RootLayout({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    const saved = window.localStorage.getItem("voc-theme");
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;
    const nextTheme: "light" | "dark" =
      saved === "dark" || saved === "light"
        ? (saved as "light" | "dark")
        : prefersDark
          ? "dark"
          : "light";
    setTheme(nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  }, []);

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
    window.localStorage.setItem("voc-theme", nextTheme);
  }

  return (
    <html lang="zh-CN">
      <head>
        <title>路特外部社媒聆听洞察中台</title>
        <meta
          name="description"
          content="母婴跨境电商外部社媒声音聆听与竞品洞察中台 — Lute Outside VOC Insight"
        />
        <meta
          name="theme-color"
          media="(prefers-color-scheme: light)"
          content="#f5f8f7"
        />
        <meta
          name="theme-color"
          media="(prefers-color-scheme: dark)"
          content="#0b1220"
        />
      </head>
      <body>
        <a href="#main-content" className="skip-link">
          跳到主内容
        </a>
        <NavBar theme={theme} onToggleTheme={toggleTheme} />
        <main id="main-content" className="page-shell">
          {children}
        </main>
      </body>
    </html>
  );
}
