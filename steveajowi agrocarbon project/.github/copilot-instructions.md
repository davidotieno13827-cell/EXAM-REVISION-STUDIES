# Ajowi AgroCarbon Token MRV

This workspace is a React + Vite + TypeScript prototype for the Ajowi AgroCarbon Token monitoring, reporting, and verification flow.

Use the existing structure as the source of truth:
- `src/App.tsx` for the dashboard UI and workflow sections
- `src/data.ts` for mock farms, measurements, verification items, and token batches
- `src/types.ts` for shared domain types
- `src/styles.css` for the visual system

Guidance for future edits:
- Keep the UI modern, clear, and data-heavy.
- Prefer small, focused components and mock data while backend services are still undefined.
- Preserve the MRV workflow: monitoring, reporting, verification, and tokenization.
- Avoid adding dependencies unless they directly support the product.
