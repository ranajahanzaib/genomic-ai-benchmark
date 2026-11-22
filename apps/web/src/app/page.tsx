/** The interactive research workspace remains a static client bundle in public/. */
export default function Home() {
  return (
    <iframe
      className="workspace"
      src="/index.html"
      title="Genomic AI Benchmark research workspace"
    />
  );
}
