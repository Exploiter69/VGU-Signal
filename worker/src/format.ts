import {escapeHtml} from "./telegram";

import type {InfoRow} from "./queries";

export function formatInfo(item: InfoRow, index?: number): string {
  const prefix = index === undefined ? "" : `<b>${index}. </b>`;
  const dates = [
    item.due_at ? `Due: ${item.due_at}` : "",
    item.starts_at ? `Starts: ${item.starts_at}` : "",
    item.ends_at ? `Ends: ${item.ends_at}` : "",
  ].filter(Boolean).join(" · ");
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
    `<b>${escapeHtml(item.category)}</b> · ${escapeHtml(item.importance)} · ${escapeHtml(item.urgency)}`,
    dates ? escapeHtml(dates) : "",
    `Verification: <b>officially verified</b>`,
    `State: ${escapeHtml(state)}`,
    `Source: <a href="${escapeHtml(item.primary_source_url)}">official source</a>`,
  ].filter(Boolean).join("\n");
}

export function formatList(title: string, items: InfoRow[]): string {
  if (!items.length) return `<b>${escapeHtml(title)}</b>\nNo matching verified information found.`;
  return [`<b>${escapeHtml(title)}</b>`, ...items.map((item, index) => formatInfo(item, index + 1))].join("\n\n");
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
  ].join("\n");
}
