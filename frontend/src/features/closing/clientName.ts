// frontend/src/features/closing/clientName.ts
import { createContext, useContext } from "react";

/** The client whose deck is being rendered, for the slide chrome (footers, cover).
 *
 *  Its own module because `react-refresh/only-export-components` forbids exporting a
 *  non-component from a component file. Exists so the deck stops hardcoding a client
 *  name: the footer read "Marchini Botelho Caselta" on every slide, so any other
 *  client's exported PDF would have carried MBC's name. */
export const ClientNameCtx = createContext<string>("");

export function useClientName(): string {
  return useContext(ClientNameCtx);
}
