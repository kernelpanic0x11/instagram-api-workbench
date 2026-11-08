function element(tag, text, attributes = {}) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  return node;
}

export function filterCoverageEntries(ledger, filter = 'all', query = '') {
  const search = query.toLowerCase();
  return [...ledger.operations, ...(ledger.unresolvedPaths ?? [])].filter(operation =>
    `${operation.method ?? 'unknown'} ${operation.path} ${(operation.fields ?? []).join(' ')} ${(operation.responseFields ?? []).join(' ')}`.toLowerCase().includes(search) &&
    (filter === 'all' || filter === 'methods' && operation.method === null ||
     filter === 'request' && operation.request === 'unresolved' ||
     filter === 'response' && operation.response === 'unresolved' || filter === 'encoding' && operation.encoding === 'unresolved' ||
     filter === 'errors' && operation.method !== null && !operation.errorParserBound ||
     filter === 'live' && operation.live === 'observed-success' || filter === 'failed' && operation.latestLiveOutcome === 'not-verified' ||
     filter.startsWith('dimension:') && operation.unresolvedDimensions?.includes(filter.slice('dimension:'.length))));
}

export async function mountCoverage() {
  if (document.querySelector('#operation-coverage')) return;
  const response = await fetch('coverage.json', {cache: 'no-store'});
  if (!response.ok) throw new Error('Could not load operation coverage');
  const ledger = await response.json(), summary = ledger.summary;
  const panel = element('section', undefined, {id: 'operation-coverage', class: 'swagger-ui wrapper coverage-panel'});
  panel.append(element('h3', 'Operation coverage'), element('p',
    `${summary.liveSuccessObservations} historical successful reads · ${summary.unsuccessfulReadObservations} reads without verified success · ${summary.documentedOperations} traced operations · ${summary.unresolvedMethodPaths} unknown-method candidates · ${summary.operationsWithRecoveredFields} with request fields · ${summary.operationsWithPartialResponseModels} partial response models · ${summary.operationsWithFinalizedEncoding} encoding traces.`),
    element('p', 'Every traced operation is included in Swagger. Client evidence and historical success describe bounded profiles. Required fields, authentication, signatures, message types and alternate responses still have gaps; no complete server contract or continuing availability guarantee is established.'));
  const search = element('input', undefined, {'aria-label': 'Filter operations and route candidates', placeholder: 'Filter by method, path or field…'});
  const filter = element('select', undefined, {'aria-label': 'Filter operation readiness'});
  for (const [value, label] of [['all', 'All operations and route candidates'], ['methods', 'HTTP method unresolved'], ['request', 'Request fields unresolved'], ['response', 'Response model unresolved'], ['encoding', 'Encoding unresolved'], ['errors', 'Error parser unresolved'], ['live', 'Historical live success'], ['failed', 'Latest test not verified']]) filter.append(element('option', label, {value}));
  for (const [name, label] of Object.entries(ledger.contractDimensionLabels ?? {})) filter.append(element('option', 'Unresolved: ' + label, {value: 'dimension:' + name}));
  const count = element('p'), list = element('div'), more = element('button', 'Show more', {class: 'btn'});
  const download = element('a', 'Download coverage ledger', {href: 'coverage.json', download: 'instagram-operation-coverage.json'});
  panel.append(search, filter, count, list, more, element('p'));
  panel.lastChild.append(download);
  let limit = 40;
  const dimensionLabels = names => names.map(name => ledger.contractDimensionLabels?.[name] ?? name).join('; ');
  function render() {
    const matches = filterCoverageEntries(ledger, filter.value, search.value);
    count.textContent = `${matches.length} matching entries; showing ${Math.min(limit, matches.length)}.`;
    list.replaceChildren();
    for (const operation of matches.slice(0, limit)) {
      const row = element('details', undefined, {class: 'coverage-operation'});
      const unknownMethod = operation.method === null;
      const liveLabel = operation.live === 'observed-success' ? operation.latestLiveOutcome === 'not-verified' ? 'historical success; latest test not verified' : 'historical live success' : operation.live === 'not-verified' ? 'tested; not verified' : 'not live-tested';
      row.append(element('summary', unknownMethod ? 'UNKNOWN ' + operation.path + ' — method and request contract unresolved' : `${operation.method.toUpperCase()} ${operation.path} — ${operation.recoveredFieldCount} request / ${operation.recoveredResponseFieldCount} response fields · ${liveLabel}`));
      row.addEventListener('toggle', () => {
        if (!row.open || row.childNodes.length > 1) return;
        if (unknownMethod) {
          row.append(element('p', `Static route candidate with ${operation.evidenceCount} extraction evidence record(s). No HTTP method has been established; this entry has no executable Swagger operation.`));
          row.append(element('p', 'Unresolved dimensions: ' + dimensionLabels(operation.unresolvedDimensions) + '.'));
          return;
        }
        if (operation.liveAttempted || operation.testedHttpStatus !== null) row.append(element('p', 'Latest recorded read: HTTP ' + (operation.testedHttpStatus ?? 'unavailable') + (operation.latestCheckedAt ? ', ' + operation.latestCheckedAt : '') + '. Application outcome: ' + (operation.latestLiveOutcome ?? operation.live) + '.'));
        if (operation.successCheckedAt) row.append(element('p', 'Recorded successful profile: ' + operation.successCheckedAt + '. This observation does not establish availability for other users or request variants.'));
        if (operation.focusedContract) row.append(element('p', 'Focused contract: ' + operation.focusedContract + '. See Swagger for verified scope and remaining gaps.'));
        if (operation.focusedRemainingGaps?.length) row.append(element('p', 'Focused gaps: ' + operation.focusedRemainingGaps.join('; ') + '.'));
        row.append(element('p', `Request: ${operation.request}. Response: ${operation.response}. Contract: partial.`));
        if (operation.unresolvedDimensions?.length) row.append(element('p', 'Unresolved dimensions: ' + dimensionLabels(operation.unresolvedDimensions) + '.'));
        if (operation.partialDimensions?.length) row.append(element('p', 'Dimensions with partial evidence: ' + dimensionLabels(operation.partialDimensions) + '.'));
        row.append(element('p', operation.fields.length ? 'Recovered logical fields: ' + operation.fields.join(', ') : 'No literal fields recovered by this bounded pass. This does not mean the endpoint takes no parameters.'));
        row.append(element('p', operation.responseFields.length ? 'Recognized response fields: ' + operation.responseFields.join(', ') : 'No response field list recovered. Parser binding: ' + (operation.responseParserBound ? 'traced' : 'unresolved') + '.'));
        row.append(element('p', 'Fields with matched-branch client reader evidence: ' + operation.responseFieldsWithReaderCalls + '. Java return descriptors do not establish wire types.'));
        row.append(element('p', 'Encoding: ' + (operation.transportVariants.join(', ') || 'unresolved') + '. Error parser: ' + (operation.errorParserBound ? 'traced; server status availability unverified' : 'unresolved') + '.'));
        if (operation.rootRelativeClientVariant) row.append(element('p', 'A client variant uses root-relative URL routing. Review its recorded routing evidence before preparing a proxy request.'));
        row.append(element('a', 'Open Swagger operation', {href: '#/' + encodeURIComponent(operation.tags[0] || 'default') + '/' + encodeURIComponent(operation.operationId)}));
        const button = element('button', 'Prepare manual request', {class: 'btn'});
        button.onclick = () => window.useRoute(operation.path, operation.method.toUpperCase());
        row.append(button, element('p', 'Preparing a request sends nothing. Review the endpoint and supply its parameters before executing it.'));
      });
      list.append(row);
    }
    more.hidden = matches.length <= limit;
  }
  search.oninput = filter.onchange = () => {limit = 40; render();};
  more.onclick = () => {limit += 80; render();};
  document.querySelector('#live-tools').after(panel);
  render();
}
