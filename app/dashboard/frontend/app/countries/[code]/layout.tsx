import { readFileSync } from "fs";
import { join } from "path";
import type { ReactNode } from "react";

export function generateStaticParams() {
  if (process.env.NEXT_PUBLIC_STATIC_MODE !== "true") return [];
  try {
    const filePath = join(process.cwd(), "public", "data", "viz_dataset.json");
    const raw = readFileSync(filePath, "utf-8");
    const ds = JSON.parse(raw);
    return (ds.countries ?? []).map((c: { code: string }) => ({ code: c.code }));
  } catch {
    return [];
  }
}

export default function CountryCodeLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
