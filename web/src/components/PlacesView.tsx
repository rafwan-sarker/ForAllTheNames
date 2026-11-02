import { useMemo } from "react";
import { count, kindLabel, pct, rankBySongs } from "../data";
import type { Album, Category, Data, Mention, Song } from "../types";
import MapView from "./MapView";
import { SongCards } from "./Panel";

function Bars({ rows, onPick, fmt, max = 10 }: { rows: [string, number][]; onPick?: (k: string) => void; fmt?: (n: number) => string; max?: number }) {
  const top = rows.slice(0, max); const m = top[0]?.[1] ?? 1;
  return (
    <ol className="pbars">
      {top.map(([k, n]) => (
        <li key={k}>
          {onPick ? <button onClick={() => onPick(k)}>{k}</button> : <span>{k}</span>}
          <span className="pv">{fmt ? fmt(n) : n}</span>
          <i style={{ width: `${(100 * n) / m}%` }} />
        </li>
      ))}
    </ol>
  );
}

export function Tiles({ items }: { items: [string, string, string?][] }) {
  return <div className="tiles">{items.map(([l, v, sub]) => <div className="tile" key={l}><span>{l}</span><b>{v}</b>{sub && <small>{sub}</small>}</div>)}</div>;
}

export function Years({ ms, songs }: { ms: Mention[]; songs: Map<number, Song> }) {
  const ys = [...songs.values()].map((s) => s.year).filter((y): y is number => !!y);
  const y0 = Math.min(...ys), y1 = Math.max(...ys);
  const by = new Map<number, number>(); let dated = 0;
  for (const m of ms) { const y = songs.get(m.song)?.year; if (y) { by.set(y, (by.get(y) ?? 0) + 1); dated++; } }
  const mx = Math.max(1, ...by.values());
  return (
    <section className="psec">
      <h3>Mentions by year</h3><small className="muted">{dated} dated mentions</small>
      <div className="pyears">{Array.from({ length: y1 - y0 + 1 }, (_, i) => y0 + i).map((y) => <span key={y} title={`${y}: ${by.get(y) ?? 0}`}><i style={{ height: `${(100 * (by.get(y) ?? 0)) / mx}%` }} /></span>)}</div>
      <div className="pax"><span>{y0}</span><span>{y1}</span></div>
    </section>
  );
}

export default function PlacesView({ d, all, ms, songs, albums, album, selected, onPick, onAlbum, onBack, go }: {
  d: Data; all: Mention[]; ms: Mention[]; songs: Map<number, Song>; albums: Map<string, Album>; album?: Album; selected: string | null;
  onPick: (n: string) => void; onAlbum: (id: string) => void; onBack: () => void; go: (c: Category, n: string) => void;
}) {
  const rows = useMemo(() => rankBySongs(ms).map(([k, n]) => [k, n] as [string, number]), [ms]);
  const selMs = useMemo(() => (selected ? ms.filter((m) => m.name === selected) : []), [ms, selected]);
  const songTotal = album ? album.songCount : d.songs.length;
  const withPlace = new Set(ms.map((m) => m.song)).size;
  const countries = count(ms, (m) => d.places[m.name]?.country);
  const perAlbum = useMemo(() => {
    const n = new Map<string, number>(); for (const m of all) { const a = songs.get(m.song)?.album; if (a) n.set(a, (n.get(a) ?? 0) + 1); }
    return d.albums.filter((a) => a.songCount >= 5 && !a.guest).map((a) => ({ id: a.id, label: `${a.name}${a.year ? ` · ${a.year}` : ""}`, v: (n.get(a.id) ?? 0) / a.songCount })).sort((a, b) => b.v - a.v);
  }, [all, songs, d.albums]);

  let side;
  if (selected && selMs.length) {
    const yrs = selMs.map((m) => songs.get(m.song)?.year).filter(Boolean) as number[];
    const p = d.places[selected];
    side = (
      <>
        <button className="pback" onClick={onBack}>← {album ? album.name : "Overview"}</button>
        <div className="kicker">Place · {kindLabel(p?.kind ?? "")}{p?.country ? ` · ${p.country}` : ""}</div>
        <h2 className="ptitle">{selected}</h2>
        <Tiles items={[["Mentions", String(selMs.length)], ["Songs", String(new Set(selMs.map((m) => m.song)).size)], ["First", yrs.length ? String(Math.min(...yrs)) : "—"], ["Latest", yrs.length ? String(Math.max(...yrs)) : "—"]]} />
        <section className="psec"><h3>Songs</h3><SongCards ms={[...selMs].sort((a, b) => (songs.get(a.song)?.year ?? 0) - (songs.get(b.song)?.year ?? 0))} songs={songs} albums={albums} all={d.mentions} go={go} /></section>
      </>
    );
  } else if (album) {
    side = (
      <>
        <button className="pback" onClick={onBack}>← Overview</button>
        <div className="phero">
          {album.cover ? <img src={album.cover} alt={`${album.name} cover`} /> : <span className="ph">{album.guest ? "ft." : "+"}</span>}
          <div><div className="kicker">Album · {album.year ?? "various"}</div><h2 className="ptitle">{album.name}</h2></div>
        </div>
        <Tiles items={[["Mentions", String(ms.length)], ["Unique places", String(rows.length)], ["Songs with a place", pct(withPlace, songTotal), `${withPlace} of ${songTotal}`]]} />
        <section className="psec"><h3>Top places</h3><small className="muted">by songs</small><Bars rows={rows} onPick={onPick} /></section>
        <section className="psec"><h3>Songs</h3><SongCards ms={[...ms].sort((a, b) => a.song - b.song || a.line - b.line)} songs={songs} albums={albums} all={d.mentions} go={go} /></section>
      </>
    );
  } else {
    side = (
      <>
        <Tiles items={[["Mentions", ms.length.toLocaleString()], ["Unique places", String(rows.length)], ["Countries", String(countries.length)], ["Songs with a place", pct(withPlace, songTotal), `${withPlace} of ${songTotal}`]]} />
        <Years ms={ms} songs={songs} />
        <div className="pgrid">
          <section className="psec"><h3>Most-mentioned places</h3><small className="muted">by songs</small><Bars rows={rows} onPick={onPick} /></section>
          <section className="psec"><h3>Most-mentioned countries</h3><small className="muted">by songs</small><Bars rows={rankBySongs(ms.map((m) => ({ name: d.places[m.name]?.country ?? "", song: m.song })).filter((x) => x.name)).map(([k, n]) => [k, n] as [string, number])} /></section>
          <section className="psec"><h3>Places per song, by album</h3>
            <Bars rows={perAlbum.map((a) => [a.label, a.v] as [string, number])}
              fmt={(n) => n.toFixed(1)} onPick={(k) => { const a = perAlbum.find((x) => x.label === k); if (a) onAlbum(a.id); }} />
          </section>
          <section className="psec"><h3>Kind of place</h3><Bars rows={count(ms, (m) => kindLabel(m.kind))} /></section>
        </div>
        <p className="credit">Places view inspired by <a href="https://drizzy.world" target="_blank" rel="noreferrer">drizzy.world</a> by niko draca. Lyrics from Genius.</p>
      </>
    );
  }
  return (
    <div className="places">
      <div className="pside">{side}</div>
      <div className="pmap">
        <div className="maptag">{selected ?? album?.name ?? "Every place"}</div>
        <MapView rows={rows} places={d.places} selected={selected} onPick={onPick} />
      </div>
    </div>
  );
}
