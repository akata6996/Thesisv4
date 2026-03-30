export function PlaceholderPage({ title }: { title: string }) {
  return (
    <main className="mx-auto mt-10 max-w-4xl p-6">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="mt-2 text-slate-300">Page scaffold ready for Phase 6+ implementation.</p>
    </main>
  )
}
