# Next.js App Directory (`src/app`)

This document aggregates and documents all the core files located in the `src/app/` directory of the Cybersecurity Analyst frontend.

---

## Files in `src/app/`

1. [`favicon.ico`](#1-faviconico) — Browser tab icon
2. [`globals.css`](#2-globalscss) — Tailwind CSS styling & theme variables
3. [`layout.tsx`](#3-layouttsx) — Root HTML layout and font loading
4. [`page.tsx`](#4-pagetsx) — Main application page and security analysis UI

---

## 1. `favicon.ico`
* **Path**: `frontend/src/app/favicon.ico`
* **Type**: Binary icon file
* **Role**: Browser tab favicon for the web application.

---

## 2. `globals.css`
* **Path**: `frontend/src/app/globals.css`
* **Role**: Defines global CSS styling, color theme tokens, and Tailwind CSS imports.
* **Full Source Code**:

```css
@import "tailwindcss";

:root {
  --background: #f8f9fa;
  --foreground: #2d3748;
  --primary: #38a169;
  --secondary: #68d391;
  --accent: #4a5568;
  --border: #e2e8f0;
  --input-bg: #ffffff;
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-secondary: var(--secondary);
  --color-accent: var(--accent);
  --color-border: var(--border);
  --font-sans: var(--font-geist-sans);
  --font-mono: var(--font-geist-mono);
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: Arial, Helvetica, sans-serif;
}
```

---

## 3. `layout.tsx`
* **Path**: `frontend/src/app/layout.tsx`
* **Role**: The Next.js root layout. Injects Google Geist / Geist Mono fonts, includes `globals.css`, and provides page title and description metadata.
* **Full Source Code**:

```tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Cybersecurity Analyst",
  description: "Professional Python code analysis tool for cybersecurity analysis",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
```

---

## 4. `page.tsx`
* **Path**: `frontend/src/app/page.tsx`
* **Role**: The main client application view (`'use client'`). Manages user file uploads, coordinates communication with the FastAPI backend `/api/analyze` endpoint, and orchestrates `<CodeInput>` and `<AnalysisResults>`.
* **Full Source Code**:

```tsx
'use client'

import { useState } from 'react';
import { AnalysisResponse } from '@/types/security';
import CodeInput from '@/components/CodeInput';
import AnalysisResults from '@/components/AnalysisResults';

// Force relative URLs in production builds
// Only use localhost when explicitly running in development mode
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
  (process.env.NODE_ENV === 'development' && typeof window !== 'undefined' && window.location?.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : '');


/**
 * Main application page for cybersecurity code analysis
 */
export default function Home() {
  const [codeContent, setCodeContent] = useState('');
  const [fileName, setFileName] = useState('');
  const [analysisResults, setAnalysisResults] = useState<AnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.py')) {
      setFileName(file.name);
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setCodeContent(content);
        setAnalysisResults(null);
        setError(null);
      };
      reader.readAsText(file);
    } else {
      alert('Please select a Python (.py) file');
    }
  };

  const handleAnalyzeCode = async () => {
    if (!codeContent) {
      alert('Please upload a Python file first');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: codeContent }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const results: AnalysisResponse = await response.json();
      setAnalysisResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during analysis');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Cybersecurity Analyst</h1>
          <p className="text-accent mt-2">Python code analysis tool for security assessment</p>
        </header>

        <div className="grid grid-rows-2 gap-6 h-[calc(100vh-200px)]">
          <CodeInput
            codeContent={codeContent}
            fileName={fileName}
            onFileUpload={handleFileUpload}
            onAnalyzeCode={handleAnalyzeCode}
            isAnalyzing={isAnalyzing}
          />
          
          <AnalysisResults
            analysisResults={analysisResults}
            isAnalyzing={isAnalyzing}
            error={error}
          />
        </div>
      </div>
    </div>
  );
}
```
