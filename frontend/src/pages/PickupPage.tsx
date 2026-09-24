import { useState } from "react";
import { api } from "../api/client";
type O = { ticket_code: string; garment_name: string; status: string };
export default function PickupPage() {
  const [code, setCode] = useState("HR-2001");
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  async function run() {
    setMsg(""); setErr("");
    try {
      const o = await api<O>("/pickup", { method: "POST", body: JSON.stringify({ ticket_code: code }) });
      setMsg(`已取件释放：${o.ticket_code} · ${o.garment_name}`);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>取件</h2>
    <div className="toolbar">
      <input value={code} onChange={e => setCode(e.target.value)} placeholder="取件票号" />
      <button onClick={run}>取件释放占位</button>
    </div>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
  </>);
}
