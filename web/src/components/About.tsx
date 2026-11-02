import { useEffect } from "react";

const FEEDBACK = import.meta.env.VITE_FEEDBACK_URL as string | undefined;

export default function About({ onClose, songs }: { onClose: () => void; songs: number }) {
  useEffect(() => { const h = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); }; window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h); }, [onClose]);
  return (
    <div className="scrim" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="about" role="dialog" aria-label="About">
        <button className="x" onClick={onClose} aria-label="Close">✕</button>
        <h2>For All The <b>Names</b></h2>
        <p>Every place, athlete, musician, brand, woman and person Drake names in his lyrics, across {songs} songs. Pick a category, click any name, and read every bar it shows up in.</p>
        <h3>How we count</h3>
        <ul>
          <li>His albums, mixtapes, singles and loosies. Guest verses on popular songs by other artists are included when <b>Features</b> is on.</li>
          <li>Lists rank by how many songs a name appears in, so one chorus can't put a name on top.</li>
          <li>Lines from featured artists on his songs count too, and are marked "feature verse".</li>
        </ul>
        {FEEDBACK && <p><a href={FEEDBACK} target="_blank" rel="noreferrer">Missed a name? Tell us.</a></p>}
        <p className="fine">Lyrics from Genius. Places view inspired by <a href="https://drizzy.world" target="_blank" rel="noreferrer">drizzy.world</a> by niko draca. Not affiliated with Drake or OVO.</p>
      </div>
    </div>
  );
}
