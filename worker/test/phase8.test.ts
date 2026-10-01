import test from "node:test";
import assert from "node:assert/strict";
import {buildIcs, parseNaturalIntent, potentialDeadlineConflicts, utcWeekRange} from "../src/phase8.ts";

test("natural search understands category and current-week intent", () => {
  const intent = parseNaturalIntent("show my exam forms this week", new Date("2026-10-01T09:00:00Z"));
  assert.equal(intent.category, "EXAM");
  assert.equal(intent.sort, "time");
  assert.equal(intent.textQuery, "forms");
  assert.equal(intent.start, "2026-09-28T00:00:00.000Z");
  assert.equal(intent.end, "2026-10-05T00:00:00.000Z");
});

test("natural search understands next week and tomorrow", () => {
  const next = parseNaturalIntent("deadlines next week", new Date("2026-10-01T09:00:00Z"));
  assert.equal(next.category, "DEADLINE");
  assert.equal(next.start, "2026-10-05T00:00:00.000Z");
  assert.equal(next.end, "2026-10-12T00:00:00.000Z");
  const tomorrow = parseNaturalIntent("fees tomorrow", new Date("2026-10-01T09:00:00Z"));
  assert.equal(tomorrow.start, "2026-10-02T00:00:00.000Z");
});

test("this-week range starts on Monday", () => {
  assert.deepEqual(utcWeekRange(new Date("2026-10-01T09:00:00Z")), {
    start: "2026-09-28T00:00:00.000Z",
    end: "2026-10-05T00:00:00.000Z",
  });
});

test("deadline conflicts are only potential time collisions", () => {
  const groups = potentialDeadlineConflicts([
    {id: "a", due_at: "2026-10-03T09:00:00Z"},
    {id: "b", due_at: "2026-10-04T08:00:00Z"},
    {id: "c", due_at: "2026-10-10T09:00:00Z"},
  ]);
  assert.deepEqual(groups[0].item_ids, ["a", "b"]);
  assert.equal(groups.length, 1);
});

test("ics export preserves verified source links", () => {
  const ics = buildIcs([{
    id: "info:1",
    title: "Exam form deadline",
    summary: "Submit the form.",
    due_at: "2026-10-15T12:00:00.000Z",
    starts_at: null,
    ends_at: null,
    primary_source_url: "https://vgu.ac.in/notice?id=1",
  }]);
  assert.match(ics, /BEGIN:VCALENDAR/);
  assert.match(ics, /SUMMARY:Exam form deadline/);
  assert.match(ics, /URL:https:\/\/vgu.ac.in\/notice\?id=1/);
  assert.match(ics, /END:VCALENDAR/);
});
