import type { VizDataset } from "../../lib/api";
import { forwardRef } from "react";
import Link from "next/link";

interface Props {
  data: VizDataset;
}

const Top20Section = forwardRef<HTMLElement, Props>(({ data }, ref) => (
  <section id="top20" ref={ref} className="viz-section">
    <h2 className="viz-section-title">TOP20 国家深挖</h2>
    <div className="viz-chart-container">
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>国家</th>
              <th>销售额</th>
              <th>国家洞察</th>
            </tr>
          </thead>
          <tbody>
            {data.top20.map((row, i) => (
              <tr key={i}>
                <td>
                  <Link href={`/countries/${row.country_code}`}>
                    {row.country as string}
                  </Link>
                </td>
                <td className="font-mono">
                  {row.sales_amount != null
                    ? Number(row.sales_amount).toLocaleString()
                    : "—"}
                </td>
                <td className="text-sm" style={{ maxWidth: 500 }}>
                  {(row.insight as string)?.slice(0, 120)}
                  {(row.insight as string)?.length > 120 ? "..." : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </section>
));

Top20Section.displayName = "Top20Section";
export default Top20Section;
