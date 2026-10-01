import test from "node:test";
import assert from "node:assert/strict";
import {buildGroundedPrompt, cosineSimilarity, extractJsonObject, validateGroundedAnswer} from "../src/ai.ts";

const evidence = [{id:"item-1",title:"Exam form deadline",summary:"Exam form closes on 10 October 2026.",category:"EXAM",sourceUrl:"https://vgu.ac.in/example"}];

test("Phase 9 rejects citation-free answers",()=>assert.throws(()=>validateGroundedAnswer({answer:"10 October",citations:[]},evidence)));
test("Phase 9 rejects unsupported citations",()=>assert.throws(()=>validateGroundedAnswer({answer:"10 October",citations:["invented"]},evidence)));
test("Phase 9 accepts grounded citations",()=>assert.deepEqual(validateGroundedAnswer({answer:"10 October",citations:["item-1"]},evidence),{answer:"10 October",citations:["item-1"]}));
test("Phase 9 parses structured output",()=>assert.deepEqual(extractJsonObject('{"answer":"x","citations":["item-1"]}'),{answer:"x",citations:["item-1"]}));
test("Phase 9 prompt forbids unsupported facts",()=>{const p=buildGroundedPrompt("What is the fee?",evidence);assert.match(p,/only factual authority/i);assert.match(p,/Never create a deadline/i);assert.match(p,/item-1/);});
test("Phase 9 cosine similarity is deterministic",()=>{assert.equal(cosineSimilarity([1,0],[1,0]),1);assert.equal(cosineSimilarity([1,0],[0,1]),0);});
