// Ühekordne peatamiskäsk salvestile. Eraldi objekt väldib samaaegsete käskude ülekirjutamist.
export async function onRequestPost({ env, request }) {
  const { key = "" } = await request.json();
  const status = (await (await env.KUKU.get("status.json"))?.json()) || {};
  const job = (status.recording || []).find((r) => r.key === key);
  if (!job?.cancel_id || !(job.cancel_end || job.end)) return new Response("salvestust ei leitud", { status: 409 });
  const command = { key, cancel_id: job.cancel_id, end: job.cancel_end || job.end };
  await env.KUKU.put(`commands/stop/${crypto.randomUUID()}.json`, JSON.stringify(command), {
    httpMetadata: { contentType: "application/json" },
  });
  return Response.json({ stopping: true }, { status: 202, headers: { "cache-control": "no-store" } });
}
