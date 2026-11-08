import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {applyReviewedReadPlan} from './reviewed-read-plan.mjs';
import {applyRequestTransports} from './request-transports.mjs';

const read = name => JSON.parse(fs.readFileSync(new URL(name, import.meta.url)));
function fixture() {
  const sourcePlan = read('online-read-plan.json');
  const plan = {...sourcePlan, targets: sourcePlan.targets.filter(target => target.staticReview)};
  const evidence = read('bulk-trace/reviewed-read-evidence.json');
  const requestFields = read('bulk-trace/request-fields.json');
  const paths = Object.fromEntries(plan.targets.map(target => [target.path, {get: {
    description: 'Reviewed synthetic operation', responses: {default: {description: 'Unknown'}},
  }}]));
  applyRequestTransports(paths, requestFields.transports.filter(entry => paths[entry.path]), path => ({path}));
  return {paths, plan, evidence, apkSha: plan.source_apk_sha256};
}
function apply(value) {
  applyReviewedReadPlan(value.paths, value.plan, value.evidence, value.apkSha);
}

test('pinned review supplies the empty signed-query example without claiming live success', () => {
  const value = fixture();
  apply(value);
  assert.equal(value.plan.targets.length, 3);
  for (const target of value.plan.targets) {
    const operation = value.paths[target.path].get;
    const parameter = operation.parameters.find(parameter => parameter.name === 'signed_body');
    assert.equal(parameter.example, 'SIGNATURE.{}');
    assert.equal(parameter.required, false);
    assert.equal(parameter['x-requiredness-status'], 'unknown');
    assert.match(parameter.description, /Reviewed bounded test input; server defaults and requiredness remain unproven/);
    assert.equal(operation['x-reviewed-read-plan'].status, 'static-input-reviewed');
    assert.equal(operation['x-reviewed-read-plan'].caller, target.staticReview.caller);
    assert.deepEqual(operation['x-reviewed-read-plan'].query, {signed_body: 'SIGNATURE.{}'});
    assert.equal(operation['x-live-check'], undefined);
    assert.equal(operation['x-read-validation'], undefined);
  }
  const descriptions = Object.values(value.paths).map(item => item.get.parameters[0].description);
  apply(value);
  assert.deepEqual(Object.values(value.paths).map(item => item.get.parameters[0].description), descriptions);
});

test('legacy plan entries without staticReview metadata are untouched', () => {
  const paths = {'/legacy/': {get: {description: 'Original'}}};
  const before = structuredClone(paths);
  applyReviewedReadPlan(paths, {targets: [{path: '/legacy/', method: 'get', query: {}}]}, null, 'unused');
  assert.deepEqual(paths, before);
});

test('APK provenance mismatches are rejected before any review is applied', () => {
  for (const source of ['plan', 'evidence']) {
    const value = fixture();
    value[source].source_apk_sha256 = 'other-apk';
    assert.throws(() => apply(value), /provenance mismatch/);
    assert.ok(Object.values(value.paths).every(item => !item.get['x-reviewed-read-plan']));
  }
});

test('unknown routes, duplicate targets and method changes cannot inherit a review', () => {
  for (const mutate of [
    value => { delete value.paths[value.plan.targets[0].path]; },
    value => { value.evidence.reviewed_routes.shift(); },
    value => { value.plan.targets.push(structuredClone(value.plan.targets[0])); },
    value => { value.plan.targets[0].method = 'post'; },
  ]) {
    const value = fixture(); mutate(value);
    assert.throws(() => apply(value), /unknown, duplicate or unreviewed GET route/);
  }
});

test('nonempty, missing and extra query values are rejected', () => {
  for (const query of [{}, {signed_body: 'SIGNATURE.{"synthetic":1}'}, {signed_body: 'SIGNATURE.{}', extra: 'value'}, {signed_body: 'SIGNATUREX{}'}]) {
    const value = fixture(); value.plan.targets[0].query = query;
    assert.throws(() => apply(value), /incorrect empty signed payload/);
  }
  const value = fixture(); value.plan.targets[0].staticReview.endpointParameterKeys = ['synthetic'];
  assert.throws(() => apply(value), /incorrect empty signed payload/);
});

test('stale call offsets, selectors and caller provenance are rejected', () => {
  for (const mutate of [
    review => { review.factory.codeUnitOffset++; },
    review => { review.routeFinalizer.dexByteOffset += 2; },
    review => { review.factory.selector = 'LX/Other;->A00()V'; },
    review => { review.callerMethodIndex++; },
    review => { review.dex = 'other.dex'; },
  ]) {
    const value = fixture(); mutate(value.plan.targets[0].staticReview);
    assert.throws(() => apply(value), /call offset or selector|caller provenance mismatch/);
  }
  const value = fixture(), review = value.plan.targets[0].staticReview;
  const instruction = value.evidence.methods[review.caller].instructions.find(instruction => instruction.code_unit_offset === review.routeFinalizer.codeUnitOffset);
  instruction.callee = 'LX/Other;->A00()V';
  assert.throws(() => apply(value), /differs from pinned instruction proof/);
});

test('a review cannot be rebound to a different route, parser or callback', () => {
  for (const mutate of [
    (value, review) => {
      value.evidence.methods[review.caller].instructions.find(instruction => instruction.string === value.plan.targets[0].path.slice(1)).string = 'other/route/';
    },
    (value, review) => { review.parser = value.plan.targets[1].staticReview.parser; },
    (value, review) => { review.callback = value.plan.targets[1].staticReview.callback; },
  ]) {
    const value = fixture(); mutate(value, value.plan.targets[0].staticReview);
    assert.throws(() => apply(value), /route literal is not bound|parser or callback differs/);
  }
});

test('unfinalized, plain, body or differently bound transport evidence is rejected', () => {
  for (const mutate of [
    variant => { variant.status = 'partial'; },
    variant => { variant.envelope = 'plain'; },
    variant => { variant.parameter_location = 'form-body'; },
    variant => { variant.evidence = []; },
    variant => { variant.evidence.forEach(record => { record.code_unit_offset++; }); },
  ]) {
    const value = fixture();
    const operation = value.paths[value.plan.targets[0].path].get;
    operation['x-request-transport'].forEach(mutate);
    assert.throws(() => apply(value), /missing matching finalized signed-query variant/);
  }
});

test('missing or conflicting query parameters fail instead of inventing a request schema', () => {
  for (const mutate of [
    operation => { operation.parameters = []; },
    operation => { operation.parameters[0].required = true; },
    operation => { operation.parameters[0].schema.type = 'object'; },
  ]) {
    const value = fixture(); mutate(value.paths[value.plan.targets[0].path].get);
    assert.throws(() => apply(value), /missing or conflicting signed_body query parameter/);
  }
});

test('failure in a later target leaves all operations unchanged', () => {
  const value = fixture(), before = structuredClone(value.paths);
  value.plan.targets.at(-1).query = {signed_body: 'SIGNATURE.{"synthetic":1}'};
  assert.throws(() => apply(value), /incorrect empty signed payload/);
  assert.deepEqual(value.paths, before);
});
