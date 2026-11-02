import { useEffect, useMemo } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } from "react-leaflet";
import type { Place } from "../types";

function Fly({ to }: { to: [number, number] | null }) {
  const map = useMap();
  const lat = to?.[0], lng = to?.[1];
  useEffect(() => { if (lat != null && lng != null) map.flyTo([lat, lng], Math.max(map.getZoom(), 5), { duration: 0.8 }); }, [lat, lng, map]);
  return null;
}

export default function MapView({ rows, places, selected, onPick }: { rows: [string, number][]; places: Record<string, Place>; selected: string | null; onPick: (n: string) => void }) {
  const pts = useMemo(() => rows.map(([name, n]) => ({ name, n, p: places[name] })).filter((x) => x.p && x.p.lat != null), [rows, places]);
  const max = pts[0]?.n ?? 1;
  const sel = selected && places[selected]?.lat != null ? ([places[selected].lat!, places[selected].lng!] as [number, number]) : null;
  return (
    <MapContainer center={[30, -40]} zoom={2.5} zoomSnap={0.25} minZoom={2} worldCopyJump className="map">
      <TileLayer className="maptiles" url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={19} attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' />
      <Fly to={sel} />
      {pts.map(({ name, n, p }) => {
        const on = name === selected;
        return (
          <CircleMarker key={name} center={[p.lat!, p.lng!]} radius={3 + 16 * Math.sqrt(n / max)} eventHandlers={{ click: () => onPick(name) }}
            pathOptions={{ color: on ? "#fff" : "#e2b84b", weight: on ? 2 : 0.8, fillColor: "#e2b84b", fillOpacity: on ? 0.95 : 0.45 }}>
            <Tooltip direction="top" offset={[0, -4]}>{name} · {n}</Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
