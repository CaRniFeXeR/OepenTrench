import { MapView } from '../components/map/MapView';

export function MapPage() {
  return (
    <div className="min-h-screen bg-slate-100">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <h1 className="text-2xl font-semibold text-slate-900">Map</h1>
          <p className="mt-1 text-sm text-slate-500">Austria overview</p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <MapView className="w-full rounded-lg overflow-hidden border border-slate-200" height={500} />
      </main>
    </div>
  );
}
