import test from "node:test";
import assert from "node:assert/strict";
import {formatList} from "../src/format.ts";
import type {InfoRow} from "../src/queries.ts";

const base: InfoRow = {
  id: "item-1",
  claim_id: "claim-1",
  title: "VGU Fee Notice",
  summary: "Annual tuition: ₹2,00,000",
  category: "FEES",
  program: null,
  branch: null,
  year: null,
  semester: null,
  importance: "HIGH",
  urgency: "NONE",
  published_at: null,
  effective_from: null,
  effective_until: null,
  due_at: null,
  starts_at: null,
  ends_at: null,
  primary_source_url: "https://vgu.ac.in/fees",
  supersedes_item_id: null,
  changed_from_item_id: null,
  corrected_item_id: null,
  claim_state: "VERIFIED",
};

test("student-facing list groups facts from the same official notice", () => {
  const first = {...base};
  const second = {...base, id: "item-2", claim_id: "claim-2", summary: "Registration fee: ₹2,500/semester"};
  const output = formatList("Verified FEES results", [first, second]);

  assert.match(output, /Verified VGU fees information/);
  assert.match(output, /• Annual tuition: ₹2,00,000/);
  assert.match(output, /• Registration fee: ₹2,500\/semester/);
  assert.match(output, /Official VGU source/);
  assert.doesNotMatch(output, /Importance/);
});

test("student-facing list does not invent missing facts", () => {
  const output = formatList("Verified FEES results", [base]);
  assert.match(output, /Annual tuition: ₹2,00,000/);
  assert.doesNotMatch(output, /Duration/);
  assert.doesNotMatch(output, /Total tuition/);
  assert.doesNotMatch(output, /Hostel/);
});
