import { useMemo, useState } from "react";
import { count, kindLabel, pct } from "../data";
import { Tiles, Years } from "./PlacesView";
import type { Album, Mention, Song } from "../types";

/** Ranked names, each followed by the covers of the albums he says it on (oldest first). */
export default function Board({ ms, songs, albums, order, title, selected, onPick, songTotal }: {
  ms: Mention[]; songs: Map<number, Song>; albums: Map<string, Album>; order: string[]; title: string; selected: string | null; onPick: (n: string) => void;
  songTotal: number;
}) {
  const [f, setF] = useState(""); const [limit, setLimit] = useState(60);
  const rows = useMemo(() => {
    const by = new Map<string, Mention[]>();
    for (const m of ms) (by.get(m.name) ?? by.set(m.name, []).get(m.name)!).push(m);
    return [...by.entries()].map(([name, list]) => {
      const al = new Map<string, number>();
      for (const m of list) { const a = songs.get(m.song)?.album ?? "other"; al.set(a, (al.get(a) ?? 0) + 1); }
      const covers = [...al.keys()].sort((a, b) => order.indexOf(a) - order.indexOf(b)).map((id) => albums.get(id)!).filter(Boolean);
      return { name, n: new Set(list.map((m) => m.song)).size, total: list.length, kind: count(list, (m) => m.kind)[0]?.[0] ?? "", covers };
    }).sort((a, b) => b.n - a.n || b.total - a.total || a.name.localeCompare(b.name));
  }, [ms, songs, albums, order]);
  const withIt = new Set(ms.map((m) => m.song)).size;
  const topKind = count(ms, (m) => kindLabel(m.kind))[0];
  const shown = rows.filter((r) => !f || r.name.toLowerCase().includes(f.toLowerCase()));
  return (
    <div className="board">
      <div className="bhead">
        <h1>{title}</h1>
        <span className="muted">{rows.length} names · ranked by number of songs</span>
        <input className="bfilter" placeholder="Find a name" value={f} onChange={(e) => setF(e.target.value)} />
      </div>
      <div className="bstats">
        <Tiles items={[["Mentions", ms.length.toLocaleString()], ["Names", String(rows.length)],
          ["Of songs", pct(withIt, songTotal), `${withIt} of ${songTotal}`],
          ["Most common", topKind ? topKind[0] : "—", topKind ? `${topKind[1]} mentions` : ""]]} />
        <Years ms={ms} songs={songs} />
      </div>
      <ol>
        {shown.slice(0, limit).map((r) => (
          <li key={r.name}>
            <button className={"brow" + (r.name === selected ? " on" : "")} onClick={() => onPick(r.name)}>
              <span className="brank">{rows.indexOf(r) + 1}</span>
              <span className="bname"><b>{r.name}</b><small>{kindLabel(r.kind)} · {r.total} {r.total === 1 ? "mention" : "mentions"}</small></span>
              <span className="bn">{r.n}<small>{r.n === 1 ? "song" : "songs"}</small></span>
              <span className="bcovers">
                {r.covers.slice(0, 10).map((a) => a.cover
                  ? <img key={a.id} src={a.cover} alt={a.name} title={a.name} loading="lazy" />
                  : <span key={a.id} className="bph" title={a.name}>{a.guest ? "ft." : "+"}</span>)}
                {r.covers.length > 10 && <span className="bmore">+{r.covers.length - 10}</span>}
              </span>
            </button>
          </li>
        ))}
      </ol>
      {shown.length > limit && <button className="more" onClick={() => setLimit(limit + 100)}>Show more</button>}
    </div>
  );
}
