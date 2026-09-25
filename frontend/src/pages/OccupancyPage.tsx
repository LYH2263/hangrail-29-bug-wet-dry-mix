import { useEffect, useState } from "react";
import { api } from "../api/client";
import { pieceMark } from "../dryCopy";
type Rail = { id: number; label: string; length_cm: number };
type Seg = { ticket_code: string; garment_name: string; dry_state: string | null; start_cm: number; end_cm: number };
type Occ = { rail_id: number; label: string; length_cm: number; rail_dry_state: string | null; segments: Seg[] };

// 杆属性直接采用后端 rail_dry_state —— 与上杆隔离判定同一来源，保证图、列表、上杆结果一致
function railStateText(s: string | null, count: number) {
  if (!count) return "空杆";
  if (s === "wet") return "湿衣杆";
  if (s === "mixed") return "干湿混挂（历史遗留）";
  return "干衣杆";
}
function railStateClass(s: string | null, count: number) {
  if (!count) return "rail-state rail-state--empty";
  if (s === "wet") return "rail-state rail-state--wet";
  if (s === "mixed") return "rail-state rail-state--mixed";
  return "rail-state rail-state--dry";
}
function segClass(s: string | null) {
  return s === "wet" ? "seg seg--wet" : "seg seg--dry";
}

export default function OccupancyPage() {
  const [rails, setRails] = useState<Rail[]>([]);
  const [maps, setMaps] = useState<Occ[]>([]);
  useEffect(() => {
    api<Rail[]>("/rails").then(async rs => {
      setRails(rs);
      const all = await Promise.all(rs.map(r => api<Occ>(`/occupancy/${r.id}`)));
      setMaps(all);
    });
  }, []);
  return (<>
    <h2>占位图（横向尺线）</h2>
    {maps.map(m => (
      <div className="ruler-wrap" key={m.rail_id}>
        <div className="ruler-label">
          <span>{m.label}
            <span className={railStateClass(m.rail_dry_state, m.segments.length)}>
              {railStateText(m.rail_dry_state, m.segments.length)}
            </span>
          </span>
          <span className="mono">0 — {m.length_cm} cm</span>
        </div>
        <div className="ruler">
          {m.segments.map((s, i) => (
            <div key={i} className={segClass(s.dry_state)} style={{ left: `${(s.start_cm / m.length_cm) * 100}%`, width: `${((s.end_cm - s.start_cm) / m.length_cm) * 100}%` }}
              title={`${s.ticket_code} ${s.start_cm}-${s.end_cm}cm · ${s.dry_state === "wet" ? "湿衣" : "干衣"}`}>
              <span className="seg-state">{pieceMark(s.dry_state)}</span>{s.garment_name}
            </div>
          ))}
        </div>
      </div>
    ))}
    {!rails.length && <p>暂无挂杆</p>}
  </>);
}
