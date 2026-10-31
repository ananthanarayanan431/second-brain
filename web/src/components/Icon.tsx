import type { ReactNode } from "react";

/*
 * A small line-icon set drawn for Neramind, matching the hand-drawn illustrations:
 * 24px grid, 1.75 round strokes, and currentColor so each icon takes the colour of
 * its surroundings (usually text-accent).
 */
const PATHS = {
  clock: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  mind: (
    <>
      <circle cx="6" cy="7" r="2.2" />
      <circle cx="18" cy="7" r="2.2" />
      <circle cx="12" cy="17" r="2.2" />
      <path d="M8.2 7h7.6M7.1 9l3.8 6M16.9 9l-3.8 6" />
    </>
  ),
  compass: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M15.5 8.5l-2 5-5 2 2-5z" />
    </>
  ),
  eye: (
    <>
      <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  hourglass: (
    <path d="M6 3h12M6 21h12M7.5 3v2.5c0 1.8 1 3.2 2.5 4.3L12 12l-2 2.2c-1.5 1.1-2.5 2.5-2.5 4.3V21M16.5 3v2.5c0 1.8-1 3.2-2.5 4.3L12 12l2 2.2c1.5 1.1 2.5 2.5 2.5 4.3V21" />
  ),
  bulb: (
    <path d="M9.5 18h5M10.5 21h3M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2v.5h5V16c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3z" />
  ),
  lock: (
    <>
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11V7.5a4 4 0 0 1 8 0V11" />
    </>
  ),
  sprout: (
    <path d="M12 21v-9M12 12c0-4-3-6.5-7-6.5 0 4 3 6.5 7 6.5zM12 10c0-3 2.5-5.5 6.5-5.5 0 3.5-2.5 5.5-6.5 5.5z" />
  ),
  message: <path d="M5 5h14a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H10l-5 4V6a1 1 0 0 1 1-1z" />,
} satisfies Record<string, ReactNode>;

export type IconName = keyof typeof PATHS;

export function Icon({ name, className = "h-5 w-5" }: { name: IconName; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  );
}

/** An icon in a soft rounded tile, used to head cards. */
export function IconTile({ name }: { name: IconName }) {
  return (
    <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-line bg-raised text-accent">
      <Icon name={name} className="h-5 w-5" />
    </span>
  );
}
