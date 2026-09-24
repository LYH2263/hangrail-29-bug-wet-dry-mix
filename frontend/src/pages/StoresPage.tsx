import { useEffect, useState } from "react";
import { api } from "../api/client";
type S = { id: number; name: string };
export default function StoresPage() {
  const [rows, setRows] = useState<S[]>([]);
  useEffect(() => { api<S[]>("/stores").then(setRows); }, []);
  return (<>
    <h2>门店</h2>
    <table className="table"><thead><tr><th>ID</th><th>名称</th></tr></thead>
    <tbody>{rows.map(s => <tr key={s.id}><td>{s.id}</td><td>{s.name}</td></tr>)}</tbody></table>
  </>);
}
