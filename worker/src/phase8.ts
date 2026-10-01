export type NaturalIntent = {
  textQuery: string;
  category?: string;
  start?: string;
  end?: string;
  sort: "relevance" | "time";
};

const CATEGORY_ALIASES: Record<string, string> = {
  deadline: "DEADLINE", deadlines: "DEADLINE",
  exam: "EXAM", exams: "EXAM", examination: "EXAM",
  fee: "FEES", fees: "FEES",
  registration: "REGISTRATION", registrations: "REGISTRATION",
  notice: "NOTICE", notices: "NOTICE", circular: "NOTICE", circulars: "NOTICE",
  event: "EVENT", events: "EVENT",
  holiday: "HOLIDAY", holidays: "HOLIDAY",
  calendar: "CALENDAR", calendars: "CALENDAR",
};

const STOPWORDS = new Set([
  "a", "an", "and", "are", "at", "be", "by", "for", "from", "in", "is",
  "me", "my", "of", "on", "or", "please", "show", "tell", "the", "to",
  "what", "when", "which", "with", "this", "week", "next", "today",
  "tomorrow", "upcoming", "soon", "important", "near", "due", "date",
]);

function isoDay(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function startOfUtcWeek(date: Date): Date {
  const value = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  const weekday = value.getUTCDay() || 7;
  value.setUTCDate(value.getUTCDate() - weekday + 1);
  return value;
}

export function parseNaturalIntent(query: string, now: Date): NaturalIntent {
  const original = query.trim();
  const lower = original.toLowerCase();
  const words = lower.split(/\s+/).filter(Boolean);
  const category = words.map((word) => CATEGORY_ALIASES[word]).find(Boolean);
  let start: Date | undefined;
  let end: Date | undefined;

  if (lower.includes("today")) {
    start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
    end = new Date(start.getTime() + 86400000);
  } else if (lower.includes("tomorrow")) {
    start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1));
    end = new Date(start.getTime() + 86400000);
  } else if (lower.includes("next week")) {
    start = startOfUtcWeek(now);
    start.setUTCDate(start.getUTCDate() + 7);
    end = new Date(start.getTime() + 7 * 86400000);
  } else if (lower.includes("this week")) {
    start = startOfUtcWeek(now);
    end = new Date(start.getTime() + 7 * 86400000);
  }

  const textQuery = words
    .filter((word) => !STOPWORDS.has(word) && !CATEGORY_ALIASES[word])
    .join(" ")
    .trim();

  return {
    textQuery,
    category,
    start: start?.toISOString(),
    end: end?.toISOString(),
    sort: start ? "time" : "relevance",
  };
}

export function potentialDeadlineConflicts<T extends {due_at: string | null; id: string}>(
  items: T[],
  windowHours = 24,
): Array<{due_at: string; item_ids: string[]}> {
  const deadlines = items
    .filter((item) => item.due_at)
    .map((item) => ({...item, due: new Date(item.due_at as string)}))
    .sort((a, b) => a.due.getTime() - b.due.getTime() || a.id.localeCompare(b.id));
  const groups: Array<{due_at: string; item_ids: string[]}> = [];
  for (const item of deadlines) {
    const last = groups.at(-1);
    if (!last) {
      groups.push({due_at: item.due.toISOString(), item_ids: [item.id]});
      continue;
    }
    const lastDue = new Date(last.due_at).getTime();
    if (Math.abs(item.due.getTime() - lastDue) <= windowHours * 3600000) {
      last.item_ids.push(item.id);
    } else {
      groups.push({due_at: item.due.toISOString(), item_ids: [item.id]});
    }
  }
  return groups.filter((group) => group.item_ids.length > 1);
}

function icsEscape(value: string): string {
  return value.replaceAll("\\", "\\\\").replaceAll(";", "\\;").replaceAll(",", "\\,").replaceAll(/\r?\n/g, "\\n");
}

function icsDate(value: string): string {
  return value.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
}

export function buildIcs(items: Array<{
  id: string;
  title: string;
  summary: string;
  due_at: string | null;
  starts_at: string | null;
  ends_at: string | null;
  primary_source_url: string;
}>): string {
  const events = items.flatMap((item) => {
    const start = item.starts_at ?? item.due_at;
    if (!start) return [];
    const end = item.ends_at ?? new Date(new Date(start).getTime() + 3600000).toISOString();
    return [
      "BEGIN:VEVENT",
      `UID:${icsEscape(item.id)}@vgu-signal`,
      `DTSTAMP:${icsDate(new Date().toISOString())}`,
      `DTSTART:${icsDate(start)}`,
      `DTEND:${icsDate(end)}`,
      `SUMMARY:${icsEscape(item.title)}`,
      `DESCRIPTION:${icsEscape(item.summary + "\\nSource: " + item.primary_source_url)}`,
      `URL:${icsEscape(item.primary_source_url)}`,
      "END:VEVENT",
    ].join("\r\n");
  });
  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//VGU Signal//Calendar//EN",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    ...events,
    "END:VCALENDAR",
    "",
  ].join("\r\n");
}

export function calendarTokenHashInput(token: string): Uint8Array {
  return new TextEncoder().encode(token);
}

export function utcWeekRange(now: Date): {start: string; end: string} {
  const start = startOfUtcWeek(now);
  return {start: start.toISOString(), end: new Date(start.getTime() + 7 * 86400000).toISOString()};
}

export function dayLabel(value: string): string {
  return isoDay(new Date(value));
}

export async function sha256Hex(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", calendarTokenHashInput(value));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}
