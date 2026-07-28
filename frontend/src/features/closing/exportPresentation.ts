// frontend/src/features/closing/exportPresentation.ts
/**
 * Export the presentation panel to PDF via the browser's print-to-PDF.
 *
 * No heavy dependency (no jspdf/html2canvas, no bundle bloat): we toggle a body
 * class that the print stylesheet (`@media print` in index.css) uses to show ONLY
 * the presentation, in a light theme, one slide per page. The user picks
 * "Salvar como PDF" in the print dialog. `beforeprint`/`afterprint` keep the class
 * scoped to the print itself, so a cancelled dialog leaves the app untouched.
 */
const PRINT_CLASS = "printing-presentation";

export function exportPresentationPdf(): void {
  const body = document.body;
  const cleanup = () => {
    body.classList.remove(PRINT_CLASS);
    window.removeEventListener("afterprint", cleanup);
  };
  body.classList.add(PRINT_CLASS);
  window.addEventListener("afterprint", cleanup);
  // Fallback for browsers that don't fire afterprint reliably.
  window.setTimeout(cleanup, 1000);
  window.print();
}
