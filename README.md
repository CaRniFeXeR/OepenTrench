# ÖpenTrench

**Team repository for the [Europe Tech Hackathon 2026](https://www.sustainista.net/challengeoegig) — AI Quality Control for Trench Documentation**

Fiber trench documentation is high-stakes: wrong survey data, missing photos, or unclear burial depth can invalidate warranties, shift liability, and cause expensive fiber cuts years later. **ÖpenTrench** is building an AI-powered quality-control prototype that reviews trench photo documentation, maps coverage gaps, and flags construction risk before acceptance.

> *Find the risk before it becomes expensive.*

**Challenge brief:** [sustainista.net/challengeoegig](https://www.sustainista.net/challengeoegig)

---

## The problem

| | |
|---|---|
| **€42M+** | Network asset value at risk if documentation defects stay hidden |
| **~500** | Trench photos to review for one route section |
| **50 yrs** | Planned network lifespan that depends on reliable documentation |

Manual review is slow and incomplete. Our goal is to **automate quality control before sign-off** so reviewers can act faster, with clearer evidence.

---

## What we are building

An end-to-end **AI-QC workflow** that:

1. **Ingests** trench photos and route geometry
2. **Geo-matches** image metadata to route segments
3. **Reviews** photos with AI/QC logic (ducts, bedding, depth, coverage, compliance)
4. **Classifies** each segment as complete, partial, or missing evidence
5. **Reports** results on an interactive map and in a concise summary

The prototype does not need to be production-ready, but the core pipeline must work: **images in → QC logic applied → risk output out**.

### Signals we target

- **Coverage** — route sections with no usable photo or survey evidence
- **Quality** — photos where ducts, bedding, ruler, seals, or context are unclear
- **Risk** — hotspots where missing evidence should block sign-off or trigger follow-up

### Compliance checks (from the brief)

GPS/date metadata, duct visibility, sand bedding, pipe end seals, ruler readability, privacy issues.

---

## Pipeline

```text
Photos + GeoJSON route
        │
        ▼
    Ingest & geo-match
        │
        ▼
    AI / QC review
        │
        ▼
 Green / yellow / red segments
        │
        ▼
    Map + report
```

---

## Challenge resources

| Resource | Purpose |
|----------|---------|
| **Trench photos** | Main input for AI-based documentation review |
| **GeoJSON route** | Map photo evidence to segments; find missing or weak coverage |
| **QC logic** | Automated compliance and evidence scoring |
| **Map + report** | Reviewer-friendly green / yellow / red output |

Use the links and datasets provided on the [challenge page](https://www.sustainista.net/challengeoegig).

---

## Expected deliverables

1. **AI-QC workflow** — process trench photos and produce quality classifications  
2. **Map or report** — show where evidence is complete, partial, or missing  
3. **Value case** — who uses it, what risk it reduces, why it should scale  

---

## Business angles (focus areas)

We may emphasize one or more of these, depending on what we ship at the hackathon:

- **Construction acceptance** — pre-check documentation before section sign-off  
- **Contractor accountability** — flag weak evidence while the trench is still actionable  
- **Network risk** — highlight undocumented sections for future excavation risk  
- **Reviewer productivity** — prioritize problematic segments instead of reviewing everything manually  
- **Audit trail** — structured evidence for warranty and compliance disputes  

---

## Team

**ÖpenTrench** — ViennaUP / Europe Tech Hackathon 2026

*(Add team members and roles here.)*

---

## Repository status

Early-stage hackathon repo. Implementation (ingest, geo-matching, models, map UI) will land here as we build during the event.

### Backend (FastAPI)

After installing dependencies (e.g. `uv sync`), run the API from the repo root:

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

SQLite is stored at `data/oepentrench_api.db` by default. Set **`OEPENTRENCH_SQLITE_PATH`** to override the database file path.

### Frontend (Vite + React)

After the API is running, start the dashboard from `frontend/`:

```bash
# Re-export OpenAPI when backend routes change
python scripts/export_openapi.py

cd frontend
npm install
npm run dev
```

The dev server runs at http://localhost:5173 and proxies `/projects` and `/health` to the API on port 8000. The TypeScript client is generated from `openapi/openapi.json` via `@hey-api/openapi-ts` (`npm run generate:api`).

### Planned layout

```text
.
├── README.md
├── data/              # route GeoJSON, sample photos (if not gitignored)
├── src/               # pipeline, QC checks, classification
└── ...                # app / map / report as we add them
```

---

## License

TBD — hackathon project.
