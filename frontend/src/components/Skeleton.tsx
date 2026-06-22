// frontend/src/components/Skeleton.tsx
export function Skeleton({ rows = 6 }: { rows?: number }) {
  return <div className="skeleton">{Array.from({ length: rows }).map((_, i) => <div key={i} className="skeleton-row" />)}</div>;
}
