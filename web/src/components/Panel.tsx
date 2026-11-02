import { useMemo, useState } from "react";
import type { Album, Mention, Song } from "../types";

function hl(line: string, text: string) {
  const i = text && text.length <= 25 ? line.toLowerCase().indexOf(text.toLowerCase()) : -1;
  if (i < 0) return line;
  return <>{line.slice(0, i)}<mark>{line.slice(i, i + text.length)}</mark>{line.slice(i + text.length)}</>;
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
function dedupe(lines: Mention[]) {
  const out: { m: Mention; n: number }[] = []; const at = new Map<string, number>();
  for (const m of lines) { const k = m.lineText.trim().toLowerCase(); const i = at.get(k); if (i === undefined) { at.set(k, out.length); out.push({ m, n: 1 }); } else out[i].n++; }
  return out;
}

export function Detail({ name, ms, songs, albums, onBack }: { name: string; ms: Mention[]; songs: Map<number, Song>; albums: Map<string, Album>; onBack: () => void }) {
  const sorted = useMemo(() => [...ms].sort((a, b) => (songs.get(a.song)?.year ?? 0) - (songs.get(b.song)?.year ?? 0) || a.song - b.song || a.line - b.line), [ms, songs]);
  const yrs = sorted.map((m) => songs.get(m.song)?.year).filter(Boolean) as number[];
  const span = yrs.length ? (yrs[0] === yrs[yrs.length - 1] ? `${yrs[0]}` : `${yrs[0]} to ${yrs[yrs.length - 1]}`) : "";
  return (
    <>
      <button className="back" onClick={onBack}>← All</button>
      <h2 className="dname">{name}</h2>
      <div className="dmeta">{ms.length} {ms.length === 1 ? "mention" : "mentions"} · {new Set(ms.map((m) => m.song)).size} songs{span ? ` · ${span}` : ""}</div>
      <SongCards ms={sorted} songs={songs} albums={albums} />
    </>
  );
}

export function SongCards({ ms, songs, albums }: { ms: Mention[]; songs: Map<number, Song>; albums: Map<string, Album> }) {
  const groups: { song: number; lines: Mention[] }[] = [];
  for (const m of ms) { const g = groups.find((x) => x.song === m.song); if (g) { if (!g.lines.some((x) => x.line === m.line)) g.lines.push(m); } else groups.push({ song: m.song, lines: [m] }); }
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
                  <small>{a?.guest ? `${s.primary} feat. Drake` : a?.name ?? "Single"}{s.year ? ` · ${s.year}` : ""}</small>
                </span>
              </a>
              {dedupe(lines).map(({ m, n }, i) => <p key={i} className="lyric">{hl(m.lineText.trim(), m.text)}{n > 1 && <span className="x">×{n}</span>}{m.speaker === "feature" && <span className="who">feature verse</span>}</p>)}
            </li>
          );
        })}
      </ul>
    </>
  );
}
