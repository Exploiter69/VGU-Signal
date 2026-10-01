export interface InfoRow {
  id: string;
  claim_id: string;
  title: string;
  summary: string;
  category: string;
  program: string | null;
  branch: string | null;
  year: number | null;
  semester: number | null;
  importance: string;
  urgency: string;
  published_at: string | null;
  effective_from: string | null;
  effective_until: string | null;
  due_at: string | null;
  starts_at: string | null;
  ends_at: string | null;
  primary_source_url: string;
  supersedes_item_id: string | null;
  changed_from_item_id: string | null;
  corrected_item_id: string | null;
  claim_state: string;
}

export interface PreferenceRow {
  user_id: string;
  telegram_user_id: string;
  program: string | null;
  branch: string | null;
  year: number | null;
  semester: number | null;
  categories_json: string;
  digest_enabled: number;
  reminders_enabled: number;
  muted: number;
  quiet_start: string | null;
  quiet_end: string | null;
}

export interface UserRow {
  id: string;
  telegram_user_id: string;
  status: string;
}

const CURRENT_FILTER = `
  c.state = 'VERIFIED'
  AND (i.effective_from IS NULL OR i.effective_from <= ?)
  AND (i.effective_until IS NULL OR i.effective_until > ?)
  AND NOT EXISTS (
    SELECT 1 FROM information_relationships r
    WHERE r.old_item_id = i.id
      AND r.kind = 'SUPERSEDES'
  )
`;

function infoQuery(): string {
  return `
    SELECT i.*, c.state AS claim_state
    FROM information_items i
    JOIN claims c ON c.id = i.claim_id
    WHERE ${CURRENT_FILTER}
  `;
}

function scopeConditions(preferences: PreferenceRow): {sql: string; params: unknown[]} {
  const clauses: string[] = [];
  const params: unknown[] = [];
  for (const [column, value] of [
    ["i.program", preferences.program],
    ["i.branch", preferences.branch],
    ["i.year", preferences.year],
    ["i.semester", preferences.semester],
  ] as const) {
    if (value !== null) {
      clauses.push(`(${column} IS NULL OR ${column} = ?)`);
      params.push(value);
    }
  }
  return {sql: clauses.length ? ` AND ${clauses.join(" AND ")}` : "", params};
}

export async function upsertUser(db: D1Database, telegramUserId: number): Promise<UserRow> {
  const now = new Date().toISOString();
  const id = `tg:${telegramUserId}`;
  await db.prepare(
    `INSERT INTO users(id, telegram_user_id, created_at, updated_at)
     VALUES (?, ?, ?, ?)
     ON CONFLICT(telegram_user_id) DO UPDATE SET updated_at = excluded.updated_at`,
  ).bind(id, String(telegramUserId), now, now).run();
  await db.prepare(
    `INSERT INTO user_preferences(user_id, updated_at) VALUES (?, ?)
     ON CONFLICT(user_id) DO NOTHING`,
  ).bind(id, now).run();
  return {id, telegram_user_id: String(telegramUserId), status: "ACTIVE"};
}

export async function getPreferences(
  db: D1Database,
  userId: string,
): Promise<PreferenceRow | null> {
  const row = await db.prepare(
    `SELECT u.id AS user_id, u.telegram_user_id, p.program, p.branch, p.year, p.semester,
            p.categories_json, p.digest_enabled, p.reminders_enabled, p.muted,
            p.quiet_start, p.quiet_end
     FROM users u JOIN user_preferences p ON p.user_id = u.id
     WHERE u.id = ?`,
  ).bind(userId).first<PreferenceRow>();
  return row ?? null;
}

export async function setPreference(
  db: D1Database,
  userId: string,
  field: string,
  value: unknown,
): Promise<void> {
  const allowed = new Set([
    "program", "branch", "year", "semester", "categories_json",
    "digest_enabled", "reminders_enabled", "muted", "quiet_start", "quiet_end",
  ]);
  if (!allowed.has(field)) throw new Error("unsupported preference");
  await db.prepare(
    `UPDATE user_preferences SET ${field} = ?, updated_at = ? WHERE user_id = ?`,
  ).bind(value, new Date().toISOString(), userId).run();
}

export async function setSession(
  db: D1Database,
  userId: string,
  flow: string,
  step: string,
): Promise<void> {
  await db.prepare(
    `INSERT INTO telegram_sessions(user_id, flow, step, updated_at) VALUES (?, ?, ?, ?)
     ON CONFLICT(user_id) DO UPDATE SET flow=excluded.flow, step=excluded.step,
     updated_at=excluded.updated_at`,
  ).bind(userId, flow, step, new Date().toISOString()).run();
}

export async function getSession(
  db: D1Database,
  userId: string,
): Promise<{flow: string; step: string} | null> {
  return (await db.prepare(
    "SELECT flow, step FROM telegram_sessions WHERE user_id = ?",
  ).bind(userId).first<{flow: string; step: string}>()) ?? null;
}

export async function clearSession(db: D1Database, userId: string): Promise<void> {
  await db.prepare("DELETE FROM telegram_sessions WHERE user_id = ?").bind(userId).run();
}

export async function getLatest(
  db: D1Database,
  preferences: PreferenceRow,
  now: Date,
  limit = 8,
): Promise<InfoRow[]> {
  const {sql: scopeSql, params: scopeParams} = scopeConditions(preferences);
  const categories = parseCategories(preferences.categories_json);
  const categorySql = categories.length
    ? ` AND i.category IN (${categories.map(() => "?").join(",")})`
    : "";
  const result = await db.prepare(
    infoQuery() + `${scopeSql}${categorySql}
      ORDER BY COALESCE(i.published_at, i.effective_from, i.created_at) DESC, i.id ASC
      LIMIT ?`,
  ).bind(
    now.toISOString(), now.toISOString(), ...scopeParams, ...categories, limit,
  ).all<InfoRow>();
  return result.results;
}

export async function getUpcoming(
  db: D1Database,
  preferences: PreferenceRow,
  now: Date,
  days = 30,
  limit = 8,
): Promise<InfoRow[]> {
  const {sql: scopeSql, params: scopeParams} = scopeConditions(preferences);
  const categories = parseCategories(preferences.categories_json);
  const categorySql = categories.length
    ? ` AND i.category IN (${categories.map(() => "?").join(",")})`
    : "";
  const end = new Date(now.getTime() + days * 86400000).toISOString();
  const result = await db.prepare(
    infoQuery() + `${scopeSql}${categorySql}
      AND (i.due_at IS NOT NULL OR i.starts_at IS NOT NULL)
      AND COALESCE(i.due_at, i.starts_at) >= ?
      AND COALESCE(i.due_at, i.starts_at) <= ?
      ORDER BY COALESCE(i.due_at, i.starts_at) ASC, i.id ASC
      LIMIT ?`,
  ).bind(
    now.toISOString(), now.toISOString(), ...scopeParams, ...categories,
    now.toISOString(), end, limit,
  ).all<InfoRow>();
  return result.results;
}

export async function searchInformation(
  db: D1Database,
  preferences: PreferenceRow,
  now: Date,
  query: string,
  limit = 8,
  respectPreferences = true,
): Promise<InfoRow[]> {
  const tokens = query.toLowerCase().trim().split(/\s+/).filter(Boolean);
  if (!tokens.length) return [];
  const {sql: scopedSql, params: scopedParams} = scopeConditions(preferences);
  const categories = parseCategories(preferences.categories_json);
  const scopeSql = respectPreferences ? scopedSql : "";
  const scopeParams = respectPreferences ? scopedParams : [];
  const categorySql = respectPreferences && categories.length
    ? ` AND i.category IN (${categories.map(() => "?").join(",")})`
    : "";
  const textSql = tokens.map(() =>
    "(LOWER(i.title) LIKE ? OR LOWER(i.summary) LIKE ? OR LOWER(c.statement) LIKE ?)"
  ).join(" AND ");
  const textParams = tokens.flatMap((token) => {
    const value = `%${token}%`;
    return [value, value, value];
  });
  const result = await db.prepare(
    infoQuery() + `${scopeSql}${categorySql} AND ${textSql}
      ORDER BY i.importance DESC, COALESCE(i.published_at, i.created_at) DESC, i.id ASC
      LIMIT ?`,
  ).bind(
    now.toISOString(), now.toISOString(), ...scopeParams, ...categories, ...textParams, limit,
  ).all<InfoRow>();
  return result.results;
}

export function parseCategories(value: string): string[] {
  try {
    const parsed = JSON.parse(value) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((item): item is string => typeof item === "string");
  } catch {
    return [];
  }
}

export function matchesQuietHours(now: Date, start: string | null, end: string | null): boolean {
  if (!start || !end) return false;
  const hhmm = now.toISOString().slice(11, 16);
  if (start === end) return true;
  return start < end ? hhmm >= start && hhmm < end : hhmm >= start || hhmm < end;
}


export interface VerificationCandidate extends InfoRow {
  claim_id: string;
}

export interface VerificationMatch {
  item: VerificationCandidate;
  score: number;
  reason: string;
}

function verificationTokens(value: string): Set<string> {
  const stop = new Set(["a", "an", "and", "are", "be", "by", "for", "from", "in", "is", "of", "on", "or", "that", "the", "this", "to", "with", "vgu", "notice"]);
  return new Set(
    value.toLowerCase().replace(/[^a-z0-9\s]/g, " ").split(/\s+/)
      .filter((token) => token.length >= 2 && !stop.has(token)),
  );
}

function verificationDates(value: string): Set<string> {
  const dates = new Set<string>();
  const pattern = /\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b/g;
  for (const match of value.matchAll(pattern)) {
    const year = match[3].length === 2 ? `20${match[3]}` : match[3];
    dates.add(`${year}-${match[2].padStart(2, "0")}-${match[1].padStart(2, "0")}`);
  }
  return dates;
}

export async function findVerificationMatches(
  db: D1Database,
  now: Date,
  query: string,
  limit = 5,
): Promise<{matches: VerificationMatch[]; conflictItemIds: Set<string>}> {
  const tokens = [...verificationTokens(query)].slice(0, 12);
  if (!tokens.length) return {matches: [], conflictItemIds: new Set()};
  const clauses = tokens.flatMap(() => [
    "LOWER(i.title) LIKE ?",
    "LOWER(i.summary) LIKE ?",
    "LOWER(c.statement) LIKE ?",
  ]);
  const params = tokens.flatMap((token) => {
    const value = `%${token}%`;
    return [value, value, value];
  });
  const result = await db.prepare(
    `SELECT i.*, c.state AS claim_state
     FROM information_items i
     JOIN claims c ON c.id = i.claim_id
     WHERE ${CURRENT_FILTER}
       AND (${clauses.join(" OR ")})
     ORDER BY COALESCE(i.published_at, i.effective_from, i.created_at) DESC
     LIMIT 30`,
  ).bind(now.toISOString(), now.toISOString(), ...params).all<VerificationCandidate>();

  const left = verificationTokens(query);
  const leftDates = verificationDates(query);
  const scored = result.results.map((item) => {
    const right = verificationTokens(`${item.title} ${item.summary}`);
    const overlap = [...left].filter((token) => right.has(token)).length;
    const union = new Set([...left, ...right]).size;
    const jaccard = union ? overlap / union : 0;
    const coverage = left.size ? overlap / left.size : 0;
    const candidateDates = verificationDates(
      [item.summary, item.due_at, item.starts_at, item.published_at].filter(Boolean).join(" "),
    );
    const dateBonus = [...leftDates].some((date) => candidateDates.has(date)) ? 0.15 : 0;
    const score = Math.min(1, 0.55 * jaccard + 0.30 * coverage + dateBonus);
    const reason = dateBonus ? `${overlap} shared tokens; matching date` : `${overlap} shared tokens`;
    return {item, score, reason};
  }).filter((match) => match.score >= 0.15)
    .sort((a, b) => b.score - a.score || a.item.id.localeCompare(b.item.id))
    .slice(0, limit);

  const conflictItemIds = new Set<string>();
  if (scored.length) {
    const placeholders = scored.map(() => "?").join(",");
    const conflicts = await db.prepare(
      `SELECT DISTINCT i.id
       FROM information_items i
       JOIN claims c ON c.id = i.claim_id
       JOIN claim_relationships r
         ON (r.left_claim_id = c.id OR r.right_claim_id = c.id)
       WHERE r.kind = 'CONFLICTS' AND c.id IN (
         SELECT claim_id FROM information_items WHERE id IN (${placeholders})
       )`,
    ).bind(...scored.map((match) => match.item.id)).all<{id: string}>();
    conflicts.results.forEach((row) => conflictItemIds.add(row.id));
  }
  return {matches: scored, conflictItemIds};
}
