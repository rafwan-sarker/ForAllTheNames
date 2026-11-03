import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { albumMap, rankBySongs, songMap, useData, useGuests } from "./data";
import { CATEGORIES, type Category } from "./types";
import PlacesView from "./components/PlacesView";
import Board from "./components/Board";
import Search from "./components/Search";
import About from "./components/About";
import { Albums, Detail, List } from "./components/Panel";

// default logo: an album cover we already show; drop a photo at web/public/logo.jpg to replace it
const FALLBACK_LOGO = "https://images.genius.com/b55953177013ca20466401280f855a08.1000x1000x1.png";

export default function App() {
  const d = useData(); const { guests, setGuests } = useGuests();
  const [sp, setSp] = useSearchParams();
  const cat = (CATEGORIES.some((c) => c.id === sp.get("c")) ? sp.get("c") : "place") as Category;
  const album = d.albums.some((a) => a.id === sp.get("p")) ? sp.get("p")! : "";
  const sel = sp.get("n");
  const [searching, setSearching] = useState(false);
  const [about, setAbout] = useState(false);
  const [logo, setLogo] = useState("/logo.jpg");
  const railMode = cat === "place" && sp.get("r") !== "album" ? "place" : "album";
  const set = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(sp);
    for (const [k, v] of Object.entries(patch)) { if (v) next.set(k, v); else next.delete(k); }
    setSp(next);
  };
  // jump to any name from a lyric highlight; album filter dropped so the name is always found
  const goTo = (c: Category, n: string) => set({ c, n, p: null, r: null });
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setSearching((o) => !o); }
      else if (e.key === "/" && !(e.target instanceof HTMLInputElement)) { e.preventDefault(); setSearching(true); }
    };
    window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h);
  }, []);

  const songs = useMemo(() => songMap(d), [d]);
  // newest project first; Singles and Guest Verses (no year) at the end
  const albumsNewest = useMemo(() => [...d.albums.filter((a) => a.year).reverse(), ...d.albums.filter((a) => !a.year)], [d]); const albums = useMemo(() => albumMap(d), [d]);
  const ms = useMemo(() => d.mentions.filter((m) => m.category === cat && (!album || songs.get(m.song)?.album === album)), [d, cat, album, songs]);
  const rows = useMemo(() => rankBySongs(ms).map(([k, n]) => [k, n] as [string, number]), [ms]);
  const selMs = useMemo(() => (sel ? ms.filter((m) => m.name === sel) : []), [ms, sel]);
  const label = CATEGORIES.find((c) => c.id === cat)!;
  const allPlaces = useMemo(() => d.mentions.filter((m) => m.category === "place"), [d]);
  const albumCounts = useMemo(() => { const m = new Map<string, number>(); for (const x of d.mentions) if (x.category === cat) { const a = songs.get(x.song)?.album ?? "other"; m.set(a, (m.get(a) ?? 0) + 1); } return m; }, [d, cat, songs]);
  const activeAlbum = album ? albums.get(album) : undefined;

  return (
    <div className={"app" + (cat === "place" || !(sel && selMs.length) ? " nopanel" : "")}>
      <header className="top">
        <button className="logo" onClick={() => setSp(new URLSearchParams())}>
          <img src={logo} alt="Drake" onError={() => setLogo(FALLBACK_LOGO)} />
          <span className="lt"><span>For All The <b>Names</b></span></span>
        </button>
        <nav className="cats">
          {CATEGORIES.map((c) => <button key={c.id} className={c.id === cat ? "on" : ""} onClick={() => set({ c: c.id, n: null, r: null })}>{c.plural}</button>)}
        </nav>
        <div className="tools">
          <button className="icon" onClick={() => setSearching(true)} aria-label="Search">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
          </button>
          <button className="icon qmark" onClick={() => setAbout(true)} aria-label="About this site">?</button>
          <label className="toggle" title="Include Drake's verses on other artists' songs">
            <input type="checkbox" checked={guests} onChange={(e) => setGuests(e.target.checked)} /> Features
          </label>
        </div>
      </header>

      <nav className="rail" aria-label="Albums">
        {cat === "place" && (
          <div className="rtog">
            <button className={railMode === "album" ? "on" : ""} onClick={() => set({ r: "album" })}>ALBUMS</button>
            <button className={railMode === "place" ? "on" : ""} onClick={() => set({ r: null })}>PLACES</button>
          </div>
        )}
        {railMode === "place" ? <List key={album} rows={rows} selected={sel} onPick={(n) => set({ n })} /> : <>
        <button className={"rall" + (!album ? " on" : "")} onClick={() => set({ p: null, n: null })}>
          <span>All albums</span><span className="ct">{[...albumCounts.values()].reduce((a, b) => a + b, 0).toLocaleString()}</span>
        </button>
        <Albums albums={albumsNewest} counts={albumCounts} active={album} onPick={(id) => set({ p: id === album ? null : id, n: null })} />
        </>}
      </nav>

      <main className={"stage" + (cat === "place" ? " wide" : "")}>
        {cat === "place"
          ? <PlacesView d={d} all={allPlaces} ms={ms} songs={songs} albums={albums} album={activeAlbum} selected={sel}
              onPick={(n) => set({ n })} onAlbum={(id) => set({ p: id, n: null })} onBack={() => set(sel ? { n: null } : { p: null })} go={goTo} />
          : <Board key={cat + "|" + album} ms={ms} songs={songs} albums={albums} order={albumsNewest.map((a) => a.id)} title={activeAlbum ? `${label.plural} on ${activeAlbum.name}` : label.plural} selected={sel} onPick={(n) => set({ n })}
              songTotal={activeAlbum ? activeAlbum.songCount : d.songs.length} />}
      </main>

      {cat !== "place" && sel && selMs.length > 0 && <aside className="panel">
        <Detail name={sel} ms={selMs} songs={songs} albums={albums} onBack={() => set({ n: null })} all={d.mentions} go={goTo} />
      </aside>}

      {about && <About onClose={() => setAbout(false)} songs={d.songs.length} />}
      {searching && <Search onClose={() => setSearching(false)} onPick={(c, n) => set({ c, n, p: null })} />}
    </div>
  );
}
