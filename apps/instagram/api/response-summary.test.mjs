import test from 'node:test';
import assert from 'node:assert/strict';
import {describeResponse} from './response-summary.mjs';
test('local missing session and upstream HTML 404 have distinct diagnoses',()=>{
 assert.match(describeResponse({status:401}),/No credentials loaded/);
 const text=describeResponse({status:404,upstream:true,contentType:'text/html',text:'<html>not logged in</html>'});assert.match(text,/session validity is unknown/i);assert.doesNotMatch(text,/invalid session|expired session/i);
});
test('HTTP 200 is not treated as authentication verification',()=>{
 assert.match(describeResponse({status:200,upstream:true,contentType:'application/json'}),/does not verify authentication/);
 assert.match(describeResponse({status:200,upstream:true,text:'<!DOCTYPE html><html>login</html>'}),/Session validity is unknown/);
});
