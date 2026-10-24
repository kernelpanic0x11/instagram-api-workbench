// Static caller review is separate from online acceptance and server requiredness.
export function applyRemainingReadReview(paths, review, evidence, apkHash) {
  if (review.source_apk_sha256 !== apkHash || evidence.source_apk_sha256 !== apkHash) throw new Error('Remaining-read review provenance mismatch');
  const uniquePaths = new Set(review.operations.map(entry => entry.path));
  if (review.operations.length !== 37 || uniquePaths.size !== 37) throw new Error('Expected the frozen 37-operation review');
  for (const entry of review.operations) {
    const operation = paths[entry.path]?.get;
    if (!operation || !evidence.reviewed_routes.includes(entry.path) || !entry.callers.length || !entry.callers.every(caller => evidence.methods[caller])) throw new Error('Remaining-read caller evidence missing');
    const {correctedQuery, ...publicReview} = entry;
    operation['x-remaining-read-review'] = {...publicReview, evidence: 'bulk-trace/remaining-read-evidence.json', serverRequiredness: 'unknown'};
    operation.description += '\n\n**Remaining-read review:** ' + entry.finding;
    operation.parameters ??= [];
    for (const [name, detail] of Object.entries(entry.fields)) {
      if (operation.parameters.some(parameter => parameter.in === 'query' && parameter.name === name)) continue;
      operation.parameters.push({name, in: 'query', required: false, schema: {type: 'string'},
        description: detail + ' Client-construction evidence; server requiredness unknown.', 'x-requiredness-status': 'unknown'});
    }
  }
}

export function remainingReadAudit(paths, review) {
  const operations = review.operations.map(entry => {
    const operation = paths[entry.path].get;
    return {path: entry.path, priorHttpStatus: entry.priorHttpStatus, disposition: entry.disposition,
      outcome: operation['x-live-check'] ? 'observed-success' : 'not-verified',
      latestHttpStatus: operation['x-read-validation']?.httpStatus ?? null,
      checkedAt: operation['x-read-validation']?.checkedAt ?? null, finding: entry.finding};
  });
  const count = predicate => operations.filter(predicate).length;
  return {source_apk_sha256: review.source_apk_sha256,
    scope: 'Complete review of the frozen 37-operation set. An observed success is one bounded read, not a complete contract. Deferred entries retain their prior observations.',
    summary: {reviewed: operations.length, correctedRequests: count(o => o.disposition === 'corrected-read'),
      nowSuccessful: count(o => o.outcome === 'observed-success'), stillUnverified: count(o => o.outcome !== 'observed-success'),
      deferred: count(o => o.disposition !== 'corrected-read')}, operations};
}
