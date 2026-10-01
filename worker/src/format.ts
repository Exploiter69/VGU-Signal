import {escapeHtml} from "./telegram";

import type {InfoRow} from "./queries";

function cleanFact(value: string): string {
  return value
    .replace(/\\s+/g, " ")
    .replace(/^[•▪◦*-]+\\s*/, "")
    .trim();
}

function factLines(value: string): string[] {
  const normalized = value.replace(/\\r/g, "").trim();
  if (!normalized) return [];

  const lines = normalized
    .split(/\\n+/)
    .map(cleanFact)
    .filter(Boolean);

  if (lines.length > 1) return lines;

  return normalized
    .split(/(?<=[.!?])\\s+(?=[A-Z₹])/)
    .map(cleanFact)
    .filter(Boolean);
}

function scopeLine(item: InfoRow): string | null {
  const scope = [
    item.program,
    item.branch,
    item.year ? `Year ${item.year}` : null,
    item.semester ? `Semester ${item.semester}` : null,
  ].filter(Boolean);
  return scope.length ? scope.join(" · ") : null;
}

function dateLine(item: InfoRow): string | null {
  const dates = [
    item.due_at ? `Due: ${item.due_at}` : "",
    item.starts_at ? `Starts: ${item.starts_at}` : "",
    item.ends_at ? `Ends: ${item.ends_at}` : "",
  ].filter(Boolean);
  return dates.length ? dates.join(" · ") : null;
}

export function formatInfo(item: InfoRow, index?: number): string {
  const prefix = index === undefined ? "" : `<b>${index}. </b>`;
  const scope = scopeLine(item);
  const dates = dateLine(item);
  const state = item.supersedes_item_id
    ? "Supersedes an earlier item"
    : item.changed_from_item_id
      ? "Changed from an earlier item"
      : item.corrected_item_id
        ? "Corrects an earlier item"
        : "Current";

  return [
    `${prefix}<b>${escapeHtml(item.title)}</b>`,
    escapeHtml(item.summary),
    scope ? `<b>Applies to:</b> ${escapeHtml(scope)}` : "",
    dates ? escapeHtml(dates) : "",
    `<b>Verified:</b> directly traceable to an official source`,
    `State: ${escapeHtml(state)}`,
    `Source: <a href="${escapeHtml(item.primary_source_url)}">official VGU source</a>`,
  ].filter(Boolean).join("\\n");
}

export function formatSearchList(
  category: string | undefined,
  items: InfoRow[],
): string {
  const heading = category ? `Verified VGU ${category.toLowerCase()} information` : "Verified VGU information";
  if (!items.length) {
    return `<b>${escapeHtml(heading)}</b>\\nNo matching verified information found in the current official archive.`;
  }

  const groups = new Map<string, {item: InfoRow; facts: string[]}>();
  for (const item of items) {
    const key = `${item.title}\\u0000${item.primary_source_url}`;
    const existing = groups.get(key);
    const facts = factLines(item.summary);
    if (!existing) {
      groups.set(key, {item, facts});
      continue;
    }
    for (const fact of facts) {
      if (!existing.facts.includes(fact)) existing.facts.push(fact);
    }
  }

  const sections = [...groups.values()].map(({item, facts}, index) => {
    const scope = scopeLine(item);
    const dates = dateLine(item);
    const visibleFacts = facts.slice(0, 12);
    return [
      `<b>${index + 1}. ${escapeHtml(item.title)}</b>`,
      ...visibleFacts.map((fact) => `• ${escapeHtml(fact)}`),
      scope ? `Applies to: ${escapeHtml(scope)}` : "",
      dates ? escapeHtml(dates) : "",
      `✓ Officially verified`,
      `🔗 <a href="${escapeHtml(item.primary_source_url)}">Official VGU source</a>`,
    ].filter(Boolean).join("\\n");
  });

  return [`<b>${escapeHtml(heading)}</b>`, ...sections].join("\\n\\n");
}

export function formatList(title: string, items: InfoRow[]): string {
  if (!items.length) return `<b>${escapeHtml(title)}</b>\\nNo matching verified information found.`;
  return [`<b>${escapeHtml(title)}</b>`, ...items.map((item, index) => formatInfo(item, index + 1))].join("\\n\\n");
}

export function formatPreferences(
  program: string | null,
  branch: string | null,
  year: number | null,
  semester: number | null,
  categories: string[],
  muted: number,
  reminders: number,
  digest: number,
  quietStart: string | null,
  quietEnd: string | null,
): string {
  return [
    "<b>Your VGU Signal settings</b>",
    `Program: ${escapeHtml(program ?? "not set")}`,
    `Branch: ${escapeHtml(branch ?? "not set")}`,
    `Year: ${year ?? "not set"}`,
    `Semester: ${semester ?? "not set"}`,
    `Categories: ${escapeHtml(categories.join(", ") || "none")}`,
    `Reminders: ${reminders ? "on" : "off"}`,
    `Weekly digest: ${digest ? "on" : "off"}`,
    `Muted: ${muted ? "yes" : "no"}`,
    `Quiet hours: ${quietStart && quietEnd ? `${quietStart}–${quietEnd} (UTC)` : "off"}`,
    "",
    "<b>Commands</b>",
    "/set program B.Tech",
    "/set branch CSE",
    "/set year 2",
    "/set semester 4",
    "/categories EXAM,FEES,REGISTRATION",
    "/reminders on|off",
    "/digest on|off",
    "/mute, /unmute",
    "/quiet 22:00 06:00",
  ].join("\\n");
}
