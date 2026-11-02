import { useEffect, useMemo, useRef, useState } from "react";
import { useData } from "../data";
import { CATEGORIES, type Category } from "../types";

type Res = { cat: Category; name: string; sub: string };

export default function Search({ onPick, onClose }: { onPick: (c: Category, n: string) => void; onClose: () => void }) {
  const d = useData();
  const [q, setQ] = useState(""); const [sel, setSel] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => { input.current?.focus(); }, []);
  const ents = useMemo(() => {
    const m = new Map<string, Res & { n: number; said: Set<string> }>();
    for (const x of d.mentions) {
      const k = `${x.category}|${x.name}`;
      const e = m.get(k) ?? m.set(k, { cat: x.category, name: x.name, sub: "", n: 0, said: new Set() }).get(k)!;
      e.n++; e.said.add(x.text.toLowerCase());
    }
    return [...m.values()].sort((a, b) => b.n - a.n);
  }, [d]);
  const results = useMemo(() => {
    const s = q.trim().toLowerCase(); if (s.length < 2) return [];
    const re = new RegExp(`(^|[^a-z0-9])${s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "i");
    return ents.filter((e) => re.test(e.name) || [...e.said].some((t) => re.test(t))).slice(0, 10)
      .map((e) => ({ ...e, sub: `${CATEGORIES.find((c) => c.id === e.cat)!.label} · ${e.n}` }));
  }, [q, ents]);
  useEffect(() => setSel(0), [q]);
  const go = (r?: Res) => { if (r) { onPick(r.cat, r.name); onClose(); } };
  return (
    <div className="scrim" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="search" role="dialog" aria-label="Search">
        <input ref={input} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search a name or how he says it"
          onKeyDown={(e) => {
            if (e.key === "Escape") onClose();
            else if (e.key === "ArrowDown") { e.preventDefault(); setSel((v) => Math.min(results.length - 1, v + 1)); }
            else if (e.key === "ArrowUp") { e.preventDefault(); setSel((v) => Math.max(0, v - 1)); }
            else if (e.key === "Enter") go(results[sel]);
          }} />
        {results.map((r, i) => (
          <button key={r.cat + r.name} className={"sr" + (i === sel ? " on" : "")} onMouseEnter={() => setSel(i)} onClick={() => go(r)}>
            <span>{r.name}</span><span className="muted">{r.sub}</span>
          </button>
        ))}
        {q.trim().length >= 2 && !results.length && <div className="muted pad">Nothing</div>}
      </div>
    </div>
  );
}
