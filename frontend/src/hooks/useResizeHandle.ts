import { useState, useEffect, useRef } from "preact/hooks";

const MIN_HEIGHT = 100;
const MAX_HEIGHT = 500;
const DEFAULT_HEIGHT = 300;

/**
 * Hook for a vertical resize handle that drags upward from the bottom.
 * Returns current height and a mousedown handler for the resize grip.
 */
export function useResizeHandle() {
  const [height, setHeight] = useState(DEFAULT_HEIGHT);
  const isResizing = useRef(false);
  const startY = useRef(0);
  const startHeight = useRef(0);

  function onResizeStart(e: MouseEvent) {
    e.preventDefault();
    isResizing.current = true;
    startY.current = e.clientY;
    startHeight.current = height;
    document.body.style.userSelect = "none";
  }

  useEffect(() => {
    function handleMouseMove(e: MouseEvent) {
      if (!isResizing.current) return;
      const delta = startY.current - e.clientY;
      const newHeight = Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, startHeight.current + delta));
      setHeight(newHeight);
    }

    function handleMouseUp() {
      if (isResizing.current) {
        isResizing.current = false;
        document.body.style.userSelect = "";
      }
    }

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, []);

  return { height, onResizeStart };
}
