export type Category = "place" | "athlete" | "musician" | "brand" | "woman" | "person";
export const CATEGORIES: { id: Category; label: string; plural: string }[] = [
  { id: "place", label: "Place", plural: "Places" },
  { id: "athlete", label: "Athlete", plural: "Athletes & teams" },
  { id: "musician", label: "Musician", plural: "Musicians" },
  { id: "brand", label: "Brand", plural: "Brands" },
  { id: "woman", label: "Woman", plural: "Women" },
  { id: "person", label: "Person", plural: "Other people" },
];
export interface Album { id: string; name: string; year: number | null; cover: string | null; songCount: number; guest?: boolean }
export interface Song { id: number; title: string; album: string; year: number | null; url: string; art: string | null; features: string[]; primary?: string }
export interface Mention {
  song: number; category: Category; name: string; kind: string; text: string; line: number; lineText: string; speaker: "drake" | "feature";
}
export interface Place { name: string; kind: string; country: string | null; lat: number | null; lng: number | null }
export interface Data { albums: Album[]; songs: Song[]; mentions: Mention[]; places: Record<string, Place>; built: string }
