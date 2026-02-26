export default async function globalSetup() {
  const res = await fetch('http://localhost:8000/api/v1/dev/seed?scenario=e2e_baseline', { method: 'POST' });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`DB seed failed: ${res.status} ${body}`);
  }
  process.env.E2E_HAS_SEEDED_DATA = 'true';
}
