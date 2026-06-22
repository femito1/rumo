// frontend/src/components/TableScroll.tsx
import { useEffect, useRef, useState } from "react";

/**
 * Wraps wide content (e.g. a table) and exposes a SINGLE horizontal scrollbar
 * that stays pinned to the bottom of the viewport while any part of the table
 * is on screen — so you never have to scroll down to a tall table's end to
 * reach the side scroller. The native body scrollbar is hidden (see CSS); the
 * sticky bar and the body stay in sync both ways.
 */
export function TableScroll({ children }: { children: React.ReactNode }) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const barRef = useRef<HTMLDivElement>(null);
  const [scrollWidth, setScrollWidth] = useState(0);
  const [overflowing, setOverflowing] = useState(false);
  const syncing = useRef(false);

  useEffect(() => {
    const body = bodyRef.current;
    if (!body) return;
    const measure = () => {
      setScrollWidth(body.scrollWidth);
      setOverflowing(body.scrollWidth > body.clientWidth + 1);
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(body);
    return () => ro.disconnect();
  }, [children]);

  function onBarScroll() {
    if (syncing.current || !bodyRef.current || !barRef.current) return;
    syncing.current = true;
    bodyRef.current.scrollLeft = barRef.current.scrollLeft;
    syncing.current = false;
  }
  function onBodyScroll() {
    if (syncing.current || !bodyRef.current || !barRef.current) return;
    syncing.current = true;
    barRef.current.scrollLeft = bodyRef.current.scrollLeft;
    syncing.current = false;
  }

  return (
    <div className="table-scroll">
      <div className="table-scroll-body" ref={bodyRef} onScroll={onBodyScroll}>
        {children}
      </div>
      {overflowing ? (
        <div className="table-scroll-bar" ref={barRef} onScroll={onBarScroll} aria-hidden="true">
          <div style={{ width: scrollWidth, height: 1 }} />
        </div>
      ) : null}
    </div>
  );
}
