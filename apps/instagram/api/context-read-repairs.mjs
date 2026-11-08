const DESCRIPTOR_NOTE = 'Source descriptors identify private context resolved in memory; they are not literal query values. Server requiredness and acceptance remain unproven.';

function reject(reason) {
  throw new Error('Context read repairs: ' + reason);
}

function sourceDescriptor(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value) &&
    Object.keys(value).length === 1 && typeof value.source === 'string' &&
    /^[a-z][a-z0-9-]{0,79}$/.test(value.source);
}

function sameKeys(left, right) {
  return Array.isArray(right) && [...left].sort().join('\0') === [...right].sort().join('\0');
}

// A correction describes one reviewed construction. It never marks a request
// successful or substitutes private context into a public Swagger example.
export function applyContextReadRepairs(paths, plan, review, safety, apkHash) {
  if (plan?.source_apk_sha256 !== apkHash || review?.source_apk_sha256 !== apkHash) reject('APK provenance mismatch');
  if (!Array.isArray(review.operations) || review.operations.length !== 37 ||
      new Set(review.operations.map(entry => entry.path)).size !== 37) reject('missing frozen 37-operation review');
  if (!Array.isArray(safety?.blockedRoutes)) reject('missing read-only route policy');
  if (!plan.corrections || typeof plan.corrections !== 'object' || Array.isArray(plan.corrections)) reject('missing correction map');
  const reviewed = new Map(review.operations.map(entry => [entry.path, entry]));
  const blocked = new Set(safety.blockedRoutes), prepared = [];
  for (const [id, correction] of Object.entries(plan.corrections)) {
    const operation = paths[correction?.path]?.get, entry = reviewed.get(correction?.path);
    if (!/^[a-z][a-z0-9-]{0,79}$/.test(id) || !operation || !entry || blocked.has(correction.path)) reject('unknown, blocked or unreviewed GET correction');
    if (typeof correction.evidence !== 'string' || !correction.evidence.trim()) reject('missing correction evidence');
    if (correction.purpose !== undefined && correction.purpose !== 'diagnostic-only') reject('unknown correction purpose');
    if (correction.appProfile !== undefined && (correction.appProfile !== 'pinned-apk' || !plan.appProfiles?.[correction.appProfile])) reject('unknown app profile');
    if (!correction.query || typeof correction.query !== 'object' || Array.isArray(correction.query)) reject('missing query construction');
    for (const [name, value] of Object.entries(correction.query)) {
      if (!Object.hasOwn(entry.fields ?? {}, name)) reject('query field lacks frozen-review evidence');
      if (typeof value !== 'string' && !sourceDescriptor(value)) reject('invalid public literal or context source descriptor');
    }
    prepared.push({id, correction, operation});
  }
  // Validate the complete plan before annotating any operation.
  for (const {id, correction, operation} of prepared) {
    const repairs = operation['x-context-read-repairs'] ??= [];
    const metadata = {id, purpose: correction.purpose ?? 'request-correction',
      query: structuredClone(correction.query), evidence: correction.evidence,
      note: DESCRIPTOR_NOTE};
    if (correction.appProfile) metadata.appProfile = {id: correction.appProfile, ...structuredClone(plan.appProfiles[correction.appProfile])};
    const existing = repairs.findIndex(item => item.id === id);
    if (existing < 0) repairs.push(metadata);
    else repairs[existing] = metadata;
  }
}

// Only a selected, strictly successful observation with this correction ID
// supplies examples. Source descriptors and resolved account values stay out.
export function applyContextReadRepairExamples(paths, plan, results, apkHash) {
  if (plan?.source_apk_sha256 !== apkHash || results?.source_apk_sha256 !== apkHash) reject('result provenance mismatch');
  const prepared = [];
  for (const check of results.checks ?? []) {
    if (check.outcome !== 'observed-success') continue;
    const correction = plan.corrections?.[check.correction], operation = paths[check.path]?.get;
    const attached = operation?.['x-context-read-repairs']?.find(item => item.id === check.correction);
    if (!correction || !attached || correction.path !== check.path || check.method !== 'get' ||
        !sameKeys(Object.keys(correction.query), check.queryKeys)) reject('successful observation differs from its correction');
    if (check.httpStatus !== 200 || check.instagramStatus !== 'ok' || check.contentType !== 'application/json' ||
        check.bodyKind !== 'object' || check.rawResponseSaved !== false || check.personalValuesSaved !== false ||
        check.requestBodySent !== false) reject('invalid successful correction observation');
    if (correction.purpose === 'diagnostic-only') continue;
    const selected = operation['x-live-check'];
    if (selected?.correction !== check.correction || selected.checkedAt !== check.checkedAt) continue;
    const literals = Object.fromEntries(Object.entries(correction.query).filter(([, value]) => typeof value === 'string'));
    for (const name of Object.keys(literals)) {
      if (!operation.parameters?.some(parameter => parameter.in === 'query' && parameter.name === name)) reject('successful correction lacks a reviewed query parameter');
    }
    prepared.push({operation, id: check.correction, literals});
  }
  for (const {operation, id, literals} of prepared) {
    operation['x-tested-context-query-literals'] = {correction: id, values: literals,
      note: 'Public literals from the selected successful construction. Private context values are omitted; this is not a complete executable request.'};
    for (const [name, value] of Object.entries(literals)) {
      const parameter = operation.parameters.find(item => item.in === 'query' && item.name === name);
      if (parameter.examples) parameter.examples[id] = {value, summary: 'Observed successful context correction'};
      else parameter.example = value;
    }
  }
}
