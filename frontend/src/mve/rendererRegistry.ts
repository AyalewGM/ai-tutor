import type { ComponentType } from "react";

import type { VisualSpec } from "./contracts";

export type VisualRenderer = ComponentType<{ spec: VisualSpec }>;

const renderers = new Map<string, VisualRenderer>();

export function registerRenderer(types: string | readonly string[], renderer: VisualRenderer): void {
  const kinds = typeof types === "string" ? [types] : types;
  for (const kind of kinds) {
    renderers.set(kind, renderer);
  }
}

export function getRenderer(type: string): VisualRenderer | undefined {
  return renderers.get(type);
}
