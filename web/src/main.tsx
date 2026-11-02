import { StrictMode, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App";
import { DataCtx, GuestCtx, withoutGuests } from "./data";
import type { Data } from "./types";

function Root() {
  const [data, setData] = useState<Data | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [guests, setGuestsState] = useState<boolean>(() => { try { return localStorage.getItem("guests") !== "off"; } catch { return true; } });
  const setGuests = (v: boolean) => { setGuestsState(v); try { localStorage.setItem("guests", v ? "on" : "off"); } catch { /* ignore */ } };
  const view = useMemo(() => (data && !guests ? withoutGuests(data) : data), [data, guests]);
  useEffect(() => { fetch("/data.json").then((r) => r.json()).then(setData).catch((e) => setErr(String(e))); }, []);
  if (err) return <div className="empty">Could not load data.json: {err}</div>;
  if (!view) return <div className="empty">Loading…</div>;
  return <GuestCtx.Provider value={{ guests, setGuests }}><DataCtx.Provider value={view}><BrowserRouter><App /></BrowserRouter></DataCtx.Provider></GuestCtx.Provider>;
}
createRoot(document.getElementById("root")!).render(<StrictMode><Root /></StrictMode>);
