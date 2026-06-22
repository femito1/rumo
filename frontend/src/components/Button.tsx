// frontend/src/components/Button.tsx
import type { ButtonHTMLAttributes } from "react";
export function Button({ variant = "primary", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  return <button className={`btn btn-${variant}`} {...props} />;
}
