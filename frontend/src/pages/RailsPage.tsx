import { useEffect, useState } from "react";
import { api } from "../api/client";
type R = { id: number; store_id: number; label: string; length_cm: number };
export default function RailsPage() {
  const [rows, setRows] = useState<R[]>([]);
  useEffect(() => { api<R[]>("/rails").then(setRows); }, []);
  return (<>
    <h2>挂杆</h2>
    <table className="table"><thead><tr><th>标签</th><th>门店</th><th>长度 cm</th></tr></thead>
    <tbody>{rows.map(r => <tr key={r.id}><td>{r.label}</td><td>{r.store_id}</td><td className="mono">{r.length_cm}</td></tr>)}</tbody></table>
  </>);
}
