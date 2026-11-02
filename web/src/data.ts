import { createContext, useContext } from "react";
import type { Album, Data, Song } from "./types";

export const DataCtx = createContext<Data | null>(null);
export const GuestCtx = createContext<{ guests: boolean; setGuests: (v: boolean) => void }>({ guests: true, setGuests: () => {} });
export function useGuests() { return useContext(GuestCtx); }

/** Drop guest-verse songs (and their mentions) when the toggle is off. */
export function withoutGuests(d: Data): Data {
  const guestAlbums = new Set(d.albums.filter((a) => a.guest).map((a) => a.id));
  const songs = d.songs.filter((s) => !guestAlbums.has(s.album));
  const keep = new Set(songs.map((s) => s.id));
  return { ...d, songs, albums: d.albums.filter((a) => !a.guest), mentions: d.mentions.filter((m) => keep.has(m.song)) };
}
export function useData(): Data {
  const d = useContext(DataCtx);
  if (!d) throw new Error("no data");
  return d;
}

export function count<T>(items: T[], key: (t: T) => string | null | undefined): [string, number][] {
  const m = new Map<string, number>();
  for (const it of items) { const k = key(it); if (k == null) continue; m.set(k, (m.get(k) ?? 0) + 1); }
  return [...m.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

export function songMap(d: Data): Map<number, Song> { return new Map(d.songs.map((s) => [s.id, s])); }
export function albumMap(d: Data): Map<string, Album> { return new Map(d.albums.map((a) => [a.id, a])); }

export function pct(a: number, b: number): string { return b ? Math.round((100 * a) / b) + "%" : "0%"; }

const KIND_LABEL: Record<string, string> = { nba: "NBA", nfl: "NFL", mlb: "MLB", nhl: "NHL", mma: "MMA", dj: "DJ", nba_team: "NBA team", nfl_team: "NFL team", other_team: "team", other_sport: "other sport", first_name: "first name only", love_interest: "love interest", athlete_adjacent: "sports figure" };
export const kindLabel = (k: string) => KIND_LABEL[k] ?? k.replace(/_/g, " ");

/** Rank names by how many songs they appear in (choruses can't inflate it); ties broken by total mentions. */
export function rankBySongs(ms: { name: string; song: number }[]): [string, number, number][] {
  const songs = new Map<string, Set<number>>(); const total = new Map<string, number>();
  for (const m of ms) { (songs.get(m.name) ?? songs.set(m.name, new Set()).get(m.name)!).add(m.song); total.set(m.name, (total.get(m.name) ?? 0) + 1); }
  return [...songs.entries()].map(([k, v]) => [k, v.size, total.get(k)!] as [string, number, number]).sort((a, b) => b[1] - a[1] || b[2] - a[2] || a[0].localeCompare(b[0]));
}
