# Cyber-Security Agent

## A Code Analyzer via Semgrep MCP server for Azure and GCP

![Course Image](assets/cyber.png)

_If you're looking at this in Cursor, please right click on the filename in the Explorer on the left, and select "Open preview", to view it in formatted glory._

### Welcome to the Week 3 Days 1 and 2 project..

Please clone this repo:

```bash
git clone https://github.com/ed-donner/cyber.git
```

Then open this as a project in Cursor; then head into the week3 directory and start with guide "day1.part0" - right click and select "Open Preview". You can also consult the full [Day-Wise Activity Guide](week3/day_wise_activity.md).

### Project Architecture

- **Frontend (`frontend/`)**: Next.js App Router with TypeScript and Tailwind CSS
  - `src/app/`: Core route and styling (`favicon.ico`, `globals.css`, `layout.tsx`, `page.tsx`)
  - `src/components/`: Modular React components (`AnalysisResults.tsx`, `CodeInput.tsx`, `FileUpload.tsx`)
  - `src/types/`: TypeScript interfaces (`security.ts`)
- **Backend (`backend/`)**: FastAPI application with Semgrep static security scanning and AI analysis (supports OpenAI and Google Gemini).
- **Infrastructure (`terraform/`)**: Infrastructure as Code configurations for Azure Container Apps and Google Cloud Run.

#### Keep in mind

- Please submit your community_contributions, including links to your repos, in the production repo community_contributions folder
- Regularly do a git pull to get the latest code
- Reach out in Udemy or email (ed@edwarddonner.com) if I can help!