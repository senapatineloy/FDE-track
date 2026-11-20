# Cybersecurity Analyst - Frontend

This is the Next.js (React + TypeScript + Tailwind CSS) frontend for the **Cybersecurity Analyst** web application. It allows users to upload Python files, sends the code to the FastAPI backend for security analysis (via Semgrep + AI), and displays the sorted vulnerabilities.

---

## Project Structure

```text
frontend/
├── public/                 # Static assets (SVGs, icons)
├── src/
│   ├── app/                # Next.js App Router core
│   │   ├── favicon.ico     # Application browser favicon
│   │   ├── globals.css     # Global styles and Tailwind CSS theme definitions
│   │   ├── layout.tsx      # Root HTML layout and font loading
│   │   └── page.tsx        # Main application page and UI workflow
│   ├── components/         # Modular React UI components
│   │   ├── AnalysisResults.tsx  # Renders security issues, CVSS scores, and summaries
│   │   ├── CodeInput.tsx        # Code editor and trigger button for analysis
│   │   └── FileUpload.tsx       # Drag-and-drop / file selector for Python (.py) files
│   └── types/              # TypeScript interfaces
│       └── security.ts     # Data types for analysis requests and security reports
├── next.config.ts          # Next.js configuration (static export: 'export')
├── package.json            # Node.js dependencies and scripts
├── postcss.config.mjs      # PostCSS configuration for Tailwind CSS
├── tsconfig.json           # TypeScript compiler configuration
└── README.md
```

---

## App Router Files (`src/app/`)

- **`favicon.ico`**: The browser tab icon for the web application.
- **`globals.css`**: Configures CSS variables for the color palette (`--background`, `--foreground`, `--primary`, `--secondary`, `--accent`, `--border`), fonts, and Tailwind directives.
- **`layout.tsx`**: Defines the root layout structure, loads Geist and Geist Mono Google fonts, and sets page metadata (`title: "Cybersecurity Analyst"`).
- **`page.tsx`**: The main client-side interactive component (`'use client'`). Manages file upload state, sends requests to the `/api/analyze` endpoint, handles loading and error states, and renders the `<CodeInput>` and `<AnalysisResults>` panels.

---

## Development

Run the frontend development server:

```bash
npm install
npm run dev
```

The frontend will be accessible at: [http://localhost:3000](http://localhost:3000)

> **Note**: In development mode, API requests are routed to the FastAPI backend running at `http://localhost:8000`.

---

## Production Build

The frontend is configured for static export (`output: 'export'` in `next.config.ts`), generating static HTML/CSS/JS in the `out/` folder which is served directly by FastAPI in Docker:

```bash
npm run build
```
