function element(tag, text, attributes = {}) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  return node;
}

export async function mountCoverage() {
  if (document.querySelector('#operation-coverage')) return;
  const response = await fetch('coverage.json', {cache: 'no-store'});
  if (!response.ok) throw new Error('Could not load operation coverage');
  const ledger = await response.json(), summary = ledger.summary;
  const panel = element('section', undefined, {id: 'operation-coverage', class: 'swagger-ui wrapper coverage-panel'});
  panel.append(element('h3', 'Operation coverage'), element('p',
    `${summary.liveSuccessObservations} observed successful reads · ${summary.unsuccessfulReadObservations} reads not verified · ${summary.documentedOperations} traced operations · ${summary.operationsWithRecoveredFields} with request fields · ${summary.operationsWithPartialResponseModels} partial response models · ${summary.operationsWithFinalizedEncoding} encoding traces · ${summary.operationsWithErrorParserBindings} error-parser bindings.`),
    element('p', 'Every operation below is included in Swagger. Request models remain partial: field requiredness, final encoding, signatures and response contracts may still need tracing. No operation has a fully recovered contract.'));
  const search = element('input', undefined, {'aria-label': 'Filter traced operations', placeholder: 'Filter all traced operations by path or field…'});
  const filter = element('select', undefined, {'aria-label': 'Filter operation readiness'});
  for (const [value, label] of [['all', 'All traced operations'], ['request', 'Request fields unresolved'], ['response', 'Response model unresolved'], ['encoding', 'Encoding unresolved'], ['errors', 'Error parser unresolved'], ['live', 'Observed live success'], ['failed', 'Tested but not verified']]) filter.append(element('option', label, {value}));
  const count = element('p'), list = element('div'), more = element('button', 'Show more', {class: 'btn'});
  const download = element('a', 'Download coverage ledger', {href: 'coverage.json', download: 'instagram-operation-coverage.json'});
  panel.append(search, filter, count, list, more, element('p'));
  panel.lastChild.append(download);
  let limit = 40;
  function render() {
    const query = search.value.toLowerCase();
    const matches = ledger.operations.filter(operation =>
      `${operation.path} ${operation.fields.join(' ')} ${operation.responseFields.join(' ')}`.toLowerCase().includes(query) &&
      (filter.value === 'all' || filter.value === 'request' && operation.request === 'unresolved' ||
       filter.value === 'response' && operation.response === 'unresolved' || filter.value === 'encoding' && operation.encoding === 'unresolved' ||
       filter.value === 'errors' && !operation.errorParserBound || filter.value === 'live' && operation.live === 'observed-success' || filter.value === 'failed' && operation.live === 'not-verified'));
    count.textContent = `${matches.length} matching operations; showing ${Math.min(limit, matches.length)}.`;
    list.replaceChildren();
    for (const operation of matches.slice(0, limit)) {
      const row = element('details', undefined, {class: 'coverage-operation'});
      row.append(element('summary', `${operation.method.toUpperCase()} ${operation.path} — ${operation.recoveredFieldCount} request / ${operation.recoveredResponseFieldCount} response fields · ${operation.live === 'observed-success' ? 'observed live success' : operation.live === 'not-verified' ? 'tested; not verified' : 'not live-tested'}`));
      row.addEventListener('toggle', () => {
        if (!row.open || row.childNodes.length > 1) return;
        if (operation.testedHttpStatus !== null) row.append(element('p', 'Observed HTTP status: ' + operation.testedHttpStatus + '. Application success is recorded separately.'));
        if (operation.focusedContract) row.append(element('p', 'Focused contract: ' + operation.focusedContract + '. See Swagger for verified scope and remaining gaps.'));
        row.append(element('p', `Request: ${operation.request}. Response: ${operation.response}. Contract: partial.`));
        row.append(element('p', operation.fields.length ? 'Recovered logical fields: ' + operation.fields.join(', ') : 'No literal fields recovered by this bounded pass. This does not mean the endpoint takes no parameters.'));
        row.append(element('p', operation.responseFields.length ? 'Recognized response fields: ' + operation.responseFields.join(', ') : 'No response field list recovered. Parser binding: ' + (operation.responseParserBound ? 'traced' : 'unresolved') + '.'));
        row.append(element('p', 'Fields with matched-branch client reader evidence: ' + operation.responseFieldsWithReaderCalls + '. Java return descriptors do not establish wire types.'));
        row.append(element('p', 'Encoding: ' + (operation.transportVariants.join(', ') || 'unresolved') + '. Error parser: ' + (operation.errorParserBound ? 'traced; server status availability unverified' : 'unresolved') + '.'));
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
