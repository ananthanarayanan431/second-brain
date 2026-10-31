import Image from "next/image";

/**
 * A hand-drawn Icons8 illustration (Notion Line Art style) fitted into a fixed
 * box. Every picture in a row gets the same box height, and the artwork is
 * contained, never cropped or stretched, so mixed proportions still line up.
 * Decorative by default: the surrounding heading already says what it shows.
 */
export function Illustration({
  src,
  width,
  height,
  box,
  className = "",
  priority = false,
}: {
  /** Path under /public, e.g. "/illustrations/hero.svg". */
  src: string;
  /** Intrinsic size reported by Icons8, used for the aspect ratio. */
  width: number;
  height: number;
  /** Box height in px. The artwork is scaled to fit inside it. */
  box: number;
  className?: string;
  priority?: boolean;
}) {
  return (
    <div className={`grid place-items-center ${className}`} style={{ height: box }}>
      <Image
        src={src}
        alt=""
        width={width}
        height={height}
        priority={priority}
        style={{ height: box, maxHeight: box, width: "auto", maxWidth: "100%", objectFit: "contain" }}
      />
    </div>
  );
}

/** Intrinsic sizes from the Icons8 download responses (see web/icons8.json). */
export const ART = {
  hero: { src: "/illustrations/hero.svg", width: 1600, height: 1900 },
  yours: { src: "/illustrations/yours.svg", width: 900, height: 900 },
  memory: { src: "/illustrations/memory.svg", width: 800, height: 800 },
  acts: { src: "/illustrations/acts.svg", width: 900, height: 1800 },
  grow: { src: "/illustrations/grow.svg", width: 1500, height: 1900 },
  ask: { src: "/illustrations/ask.svg", width: 1400, height: 1300 },
  search: { src: "/illustrations/search.svg", width: 1100, height: 1100 },
  noResults: { src: "/illustrations/no-results.svg", width: 1000, height: 1000 },
} as const;
