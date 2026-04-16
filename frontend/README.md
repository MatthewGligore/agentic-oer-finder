# Frontend (React + Vite)

Modern React UI for searching and reviewing OER results.

## Run Locally

```bash
npm install
npm run dev
```

Frontend URL: `http://localhost:3000`

## Scripts

- `npm run dev` - start development server
- `npm run build` - build production assets to `dist/`
- `npm run preview` - preview production build
- `npm run lint` - lint source files

## API Integration

Local dev proxy in `vite.config.js` forwards `/api` requests to `http://localhost:8000`.

Ensure backend is running before testing UI search flows.

## Project Structure (Current)

```text
src/
	components/
	context/
	layout/
	pages/
	sections/
	services/
	utils/
```

## Build Output

```bash
npm run build
```

Static artifacts are generated in `dist/`.
