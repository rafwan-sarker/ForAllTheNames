import { useMemo, useState } from "react";
import type { Album, Category, Mention, Song } from "../types";

/** Highlight every name on the line (several mentions can share one line). */
function hl(line: string, ms: Mention[], go?: (c: Category, n: string) => void) {
  const spans: [number, number, Mention][] = [];
  for (const m of ms) {
    const t = m.text;
    if (!t || t.length > 25) continue;
    // whole-word match, exact case first ("40" must not light up inside "400")
    const esc = t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const hit = new RegExp(`(?<![A-Za-z0-9])${esc}(?![A-Za-z0-9])`).exec(line) ?? new RegExp(`(?<![A-Za-z0-9])${esc}(?![A-Za-z0-9])`, "i").exec(line);
    const i = hit ? hit.index : -1;
    if (i >= 0 && !spans.some(([a, b]) => i < b && i + t.length > a)) spans.push([i, i + t.length, m]);
  }
  if (!spans.length) return line;
  spans.sort((a, b) => a[0] - b[0]);
  const out: React.ReactNode[] = []; let at = 0;
  spans.forEach(([a, b, m], k) => {
    out.push(line.slice(at, a), go
      ? <mark key={k} role="button" tabIndex={0} title={`${m.name}: see every bar`} onClick={() => go(m.category, m.name)} onKeyDown={(e) => { if (e.key === "Enter") go(m.category, m.name); }}>{line.slice(a, b)}</mark>
      : <mark key={k}>{line.slice(a, b)}</mark>);
    at = b;
  });
  out.push(line.slice(at));
  return <>{out}</>;
}

/** "feat. A, B" for Drake's songs; "Artist · feat. A" for guest verses. */
function who(s: Song, guest: boolean) {
  const others = (s.features ?? []).filter((f) => f.toLowerCase() !== "drake");
  if (guest) return `${s.primary ?? ""}${others.length ? ` · feat. ${others.join(", ")}` : ""}`;
  return others.length ? `feat. ${others.join(", ")}` : "";
}

export function Albums({ albums, counts, active, onPick }: { albums: Album[]; counts: Map<string, number>; active: string; onPick: (id: string) => void }) {
  const max = Math.max(1, ...counts.values());
  return (
    <ol className="albums">
      {albums.map((a) => {
        const n = counts.get(a.id) ?? 0;
        return (
          <li key={a.id}>
            <button className={a.id === active ? "on" : ""} onClick={() => onPick(a.id)}>
              {a.cover ? <img src={a.cover} alt="" loading="lazy" /> : <span className="ph">{a.guest ? "ft." : "+"}</span>}
              <span className="at"><b>{a.name}</b><small>{a.year ?? (a.guest ? "Other artists' songs" : "Singles & loosies")}</small></span>
              <span className="ct">{n}</span>
              <i style={{ width: `${(100 * n) / max}%` }} />
            </button>
          </li>
        );
      })}
    </ol>
  );
}

export function List({ rows, selected, onPick }: { rows: [string, number][]; selected: string | null; onPick: (n: string) => void }) {
  const [f, setF] = useState(""); const [all, setAll] = useState(false);
  const shown = rows.filter(([k]) => !f || k.toLowerCase().includes(f.toLowerCase()));
  return (
    <>
      <input className="filter" placeholder="Filter" value={f} onChange={(e) => setF(e.target.value)} />
      <ol className="list">
        {(all || f ? shown : shown.slice(0, 60)).map(([k, n]) => (
          <li key={k}>
            <button className={k === selected ? "on" : ""} onClick={() => onPick(k)}>
              <span className="nm">{k}</span><span className="ct">{n}</span>
            </button>
          </li>
        ))}
      </ol>
      {!all && !f && shown.length > 60 && <button className="more" onClick={() => setAll(true)}>All {shown.length}</button>}
    </>
  );
}

/** Collapse identical lines (choruses) inside one song into a single line with a count. */
function dedupe(lines: Mention[][]) {
  const out: { ms: Mention[]; n: number }[] = []; const at = new Map<string, number>();
  for (const ms of lines) { const k = ms[0].lineText.trim().toLowerCase(); const i = at.get(k); if (i === undefined) { at.set(k, out.length); out.push({ ms, n: 1 }); } else out[i].n++; }
  return out;
}

export function Detail({ name, ms, songs, albums, onBack, all, go }: { name: string; ms: Mention[]; songs: Map<number, Song>; albums: Map<string, Album>; onBack: () => void; all?: Mention[]; go?: (c: Category, n: string) => void }) {
  const sorted = useMemo(() => [...ms].sort((a, b) => (songs.get(a.song)?.year ?? 0) - (songs.get(b.song)?.year ?? 0) || a.song - b.song || a.line - b.line), [ms, songs]);
  const yrs = sorted.map((m) => songs.get(m.song)?.year).filter(Boolean) as number[];
  const span = yrs.length ? (yrs[0] === yrs[yrs.length - 1] ? `${yrs[0]}` : `${yrs[0]} to ${yrs[yrs.length - 1]}`) : "";
  return (
    <>
      <button className="back" onClick={onBack}>← All</button>
      <h2 className="dname">{name}</h2>
      <div className="dmeta">{ms.length} {ms.length === 1 ? "mention" : "mentions"} · {new Set(ms.map((m) => m.song)).size} songs{span ? ` · ${span}` : ""}</div>
      <SongCards ms={sorted} songs={songs} albums={albums} all={all} go={go} />
    </>
  );
}

export function SongCards({ ms, songs, albums, all, go }: { ms: Mention[]; songs: Map<number, Song>; albums: Map<string, Album>; all?: Mention[]; go?: (c: Category, n: string) => void }) {
  // every mention on a shown line (so "the W" is clickable from the Brands view too)
  const onLine = (song: number, line: number) => (all ?? ms).filter((x) => x.song === song && x.line === line);
  // per song, per line: every mention on that line
  const groups: { song: number; lines: Mention[][] }[] = [];
  for (const m of ms) {
    let g = groups.find((x) => x.song === m.song); if (!g) { g = { song: m.song, lines: [] }; groups.push(g); }
    const l = g.lines.find((x) => x[0].line === m.line); if (l) l.push(m); else g.lines.push([m]);
  }
  return (
    <>
      <ul className="cards">
        {groups.map(({ song, lines }) => {
          const s = songs.get(song); const a = s && albums.get(s.album);
          if (!s) return null;
          return (
            <li key={song} className="card">
              <a className="chead" href={s.url} target="_blank" rel="noreferrer">
                <img src={s.art ?? a?.cover ?? ""} alt="" loading="lazy" />
                <span>
                  <b>{s.title}</b>
                  <small>{a?.guest ? "Guest verse" : a && a.id !== "other" ? a.name : "Single"}{s.year ? ` · ${s.year}` : ""}</small>
                  {who(s, !!a?.guest) && <small className="who2">{who(s, !!a?.guest)}</small>}
                </span>
              </a>
              {dedupe(lines).map(({ ms: lm, n }, i) => <p key={i} className="lyric">{hl(lm[0].lineText.trim(), onLine(lm[0].song, lm[0].line), go)}{n > 1 && <span className="x">×{n}</span>}{lm[0].speaker === "feature" && <span className="who">feature verse</span>}</p>)}
            </li>
          );
        })}
      </ul>
    </>
  );
}
