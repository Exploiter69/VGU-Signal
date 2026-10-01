import {formatInfo, formatList, formatPreferences} from "./format";
import {
  clearSession,
  findVerificationMatches,
  getLatest,
  getPreferences,
  getSession,
  getUpcoming,
  matchesQuietHours,
  parseCategories,
  searchInformation,
  setPreference,
  setSession,
  upsertUser,
} from "./queries";
import {downloadFile, getFile, sendMessage} from "./telegram";
import type {TelegramUpdate} from "./telegram";

export interface Env {
  DB: D1Database;
  EVIDENCE: R2Bucket;
  TELEGRAM_BOT_TOKEN: string;
  TELEGRAM_WEBHOOK_SECRET?: string;
}

const CATEGORIES = [
  "DEADLINE", "EXAM", "FEES", "REGISTRATION", "NOTICE", "EVENT", "HOLIDAY", "CALENDAR",
] as const;

function privateChat(update: TelegramUpdate): boolean {
  return update.message?.chat.type === "private";
}

function commandParts(text: string): {command: string; args: string} {
  const [first, ...rest] = text.trim().split(/\s+/);
  return {command: first.toLowerCase().split("@")[0], args: rest.join(" ").trim()};
}

function onboardingComplete(
  program: string | null,
  branch: string | null,
  year: number | null,
  semester: number | null,
): boolean {
  return Boolean(program && branch && year && semester);
}

async function startOnboarding(
  env: Env,
  userId: string,
  chatId: number,
  token: string,
): Promise<void> {
  await setSession(env.DB, userId, "onboarding", "program");
  await sendMessage(
    token,
    chatId,
    "<b>Welcome to VGU Signal.</b>\n\nI use verified public VGU information and keep your preferences here only for relevance.\n\nFirst, send your program (for example: <code>B.Tech</code>). You can send /cancel anytime.",
  );
}

async function handleOnboarding(
  env: Env,
  userId: string,
  chatId: number,
  text: string,
  token: string,
): Promise<boolean> {
  const session = await getSession(env.DB, userId);
  if (!session || session.flow !== "onboarding") return false;
  if (text.toLowerCase() === "/cancel") {
    await clearSession(env.DB, userId);
    await sendMessage(token, chatId, "Onboarding cancelled. Use /settings whenever you want to configure preferences.");
    return true;
  }
  if (!text) {
    await sendMessage(token, chatId, "Please send a value, or /cancel.");
    return true;
  }

  switch (session.step) {
    case "program":
      await setPreference(env.DB, userId, "program", text);
      await setSession(env.DB, userId, "onboarding", "branch");
      await sendMessage(token, chatId, "Now send your branch/discipline (for example: <code>CSE</code>).");
      return true;
    case "branch":
      await setPreference(env.DB, userId, "branch", text);
      await setSession(env.DB, userId, "onboarding", "year");
      await sendMessage(token, chatId, "Send your year as a number (1–10).");
      return true;
    case "year": {
      const year = Number(text);
      if (!Number.isInteger(year) || year < 1 || year > 10) {
        await sendMessage(token, chatId, "Please send a whole year number from 1 to 10.");
        return true;
      }
      await setPreference(env.DB, userId, "year", year);
      await setSession(env.DB, userId, "onboarding", "semester");
      await sendMessage(token, chatId, "Send your semester as a number (1–20).");
      return true;
    }
    case "semester": {
      const semester = Number(text);
      if (!Number.isInteger(semester) || semester < 1 || semester > 20) {
        await sendMessage(token, chatId, "Please send a whole semester number from 1 to 20.");
        return true;
      }
      await setPreference(env.DB, userId, "semester", semester);
      await setSession(env.DB, userId, "onboarding", "categories");
      await sendMessage(
        token,
        chatId,
        "Send notification categories as comma-separated values, for example <code>EXAM,FEES,REGISTRATION,DEADLINE</code>. Use <code>ALL</code> for every category.",
      );
      return true;
    }
    case "categories": {
      const categories = parseCategoryInput(text);
      if (!categories) {
        await sendMessage(token, chatId, `Unknown category. Use: ${CATEGORIES.join(", ")} or ALL.`);
        return true;
      }
      await setPreference(env.DB, userId, "categories_json", JSON.stringify(categories));
      await clearSession(env.DB, userId);
      await sendMessage(
        token,
        chatId,
        "<b>You're set.</b>\n\nUse /latest for recent verified information, /upcoming for deadlines/events, /search for archive search, /verify to check a claim against known official information, and /settings to change preferences.",
      );
      return true;
    }
    default:
      await clearSession(env.DB, userId);
      return false;
  }
}

function parseCategoryInput(value: string): string[] | null {
  if (value.trim().toUpperCase() === "ALL") return [...CATEGORIES];
  const categories = [...new Set(value.toUpperCase().split(",").map((item) => item.trim()).filter(Boolean))];
  return categories.length && categories.every((item) => CATEGORIES.includes(item as (typeof CATEGORIES)[number]))
    ? categories
    : null;
}

async function handleSettings(env: Env, userId: string, chatId: number, token: string): Promise<void> {
  const p = await getPreferences(env.DB, userId);
  if (!p) return;
  await sendMessage(token, chatId, formatPreferences(
    p.program, p.branch, p.year, p.semester, parseCategories(p.categories_json),
    p.muted, p.reminders_enabled, p.digest_enabled, p.quiet_start, p.quiet_end,
  ));
}

async function handleSet(env: Env, userId: string, chatId: number, args: string, token: string): Promise<void> {
  const match = args.match(/^(program|branch|year|semester)\s+(.+)$/i);
  if (!match) {
    await sendMessage(token, chatId, "Usage: /set program B.Tech | /set branch CSE | /set year 2 | /set semester 4");
    return;
  }
  const field = match[1].toLowerCase();
  const value = match[2].trim();
  if (field === "year" || field === "semester") {
    const number = Number(value);
    const max = field === "year" ? 10 : 20;
    if (!Number.isInteger(number) || number < 1 || number > max) {
      await sendMessage(token, chatId, `${field} must be a whole number from 1 to ${max}.`);
      return;
    }
    await setPreference(env.DB, userId, field, number);
  } else {
    await setPreference(env.DB, userId, field, value);
  }
  await sendMessage(token, chatId, "Preference updated. Use /settings to review it.");
}

async function handleCategories(env: Env, userId: string, chatId: number, args: string, token: string): Promise<void> {
  const categories = parseCategoryInput(args);
  if (!categories) {
    await sendMessage(token, chatId, `Usage: /categories EXAM,FEES,REGISTRATION or /categories ALL. Valid: ${CATEGORIES.join(", ")}.`);
    return;
  }
  await setPreference(env.DB, userId, "categories_json", JSON.stringify(categories));
  await sendMessage(token, chatId, "Notification categories updated.");
}

async function handleToggle(
  env: Env,
  userId: string,
  chatId: number,
  field: "reminders_enabled" | "digest_enabled",
  args: string,
  label: string,
  token: string,
): Promise<void> {
  const value = args.toLowerCase();
  if (value !== "on" && value !== "off") {
    await sendMessage(token, chatId, `Usage: /${label} on|off`);
    return;
  }
  await setPreference(env.DB, userId, field, value === "on" ? 1 : 0);
  await sendMessage(token, chatId, `${label} turned ${value}.`);
}

function isValidTime(value: string): boolean {
  const [hour, minute] = value.split(":").map(Number);
  return hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59;
}

async function handleQuiet(env: Env, userId: string, chatId: number, args: string, token: string): Promise<void> {
  const match = args.match(/^(\d{2}:\d{2})\s+(\d{2}:\d{2})$/);
  if (!match || !isValidTime(match[1]) || !isValidTime(match[2])) {
    await sendMessage(token, chatId, "Usage: /quiet 22:00 06:00 (times are UTC).");
    return;
  }
  await setPreference(env.DB, userId, "quiet_start", match[1]);
  await setPreference(env.DB, userId, "quiet_end", match[2]);
  await sendMessage(token, chatId, "Quiet hours updated. Use /quiet off to disable them.");
}

async function dispatchList(
  env: Env,
  preferences: Awaited<ReturnType<typeof getPreferences>>,
  chatId: number,
  token: string,
  kind: "latest" | "upcoming",
): Promise<void> {
  if (!preferences) return;
  const items = kind === "latest"
    ? await getLatest(env.DB, preferences, new Date())
    : await getUpcoming(env.DB, preferences, new Date());
  await sendMessage(token, chatId, formatList(
    kind === "latest" ? "Latest verified VGU information" : "Upcoming deadlines and events", items,
  ));
}

async function handleSearch(
  env: Env,
  preferences: Awaited<ReturnType<typeof getPreferences>>,
  chatId: number,
  token: string,
  query: string,
  verify: boolean,
): Promise<void> {
  if (!preferences) return;
  if (!query) {
    await sendMessage(token, chatId, verify ? "Usage: /verify <claim or notice text>" : "Usage: /search <words>");
    return;
  }
  const items = await searchInformation(env.DB, preferences, new Date(), query, 6, !verify);
  if (!items.length) {
    await sendMessage(
      token,
      chatId,
      verify
        ? "<b>Not officially confirmed.</b>\n\nNo matching verified VGU information was found in the current archive. Absence of a match does not prove a claim is false."
        : "No matching verified information found.",
    );
    return;
  }
  const heading = verify
    ? "<b>Official evidence matches</b>\nThe archive contains verified information matching your text. Compare the source and dates below."
    : "<b>Verified search results</b>";
  await sendMessage(token, chatId, [heading, ...items.map((item, index) => formatInfo(item, index + 1))].join("\n\n"));
}

async function handleCommand(env: Env, userId: string, chatId: number, text: string, token: string): Promise<void> {
  const {command, args} = commandParts(text);
  const preferences = await getPreferences(env.DB, userId);
  switch (command) {
    case "/start":
      if (!preferences || !onboardingComplete(preferences.program, preferences.branch, preferences.year, preferences.semester)) {
        await startOnboarding(env, userId, chatId, token);
      } else {
        await sendMessage(token, chatId, "<b>VGU Signal is ready.</b>\nUse /latest, /upcoming, /search, /verify, or /settings.");
      }
      return;
    case "/help":
      await sendMessage(token, chatId, "<b>VGU Signal commands</b>\n/start — onboarding\n/latest — recent verified information\n/upcoming — upcoming deadlines/events\n/search &lt;words&gt; — search verified archive\n/verify &lt;text&gt; — check for matching official evidence\n/settings — preferences\n/set ... — change one preference\n/categories ... — notification categories\n/reminders on|off\n/digest on|off\n/mute and /unmute\n/quiet HH:MM HH:MM — quiet hours in UTC\n/quiet off");
      return;
    case "/latest":
      await dispatchList(env, preferences, chatId, token, "latest");
      return;
    case "/upcoming":
      await dispatchList(env, preferences, chatId, token, "upcoming");
      return;
    case "/search":
      await handleSearch(env, preferences, chatId, token, args, false);
      return;
    case "/verify":
      await handleSearch(env, preferences, chatId, token, args, true);
      return;
    case "/settings":
      await handleSettings(env, userId, chatId, token);
      return;
    case "/set":
      await handleSet(env, userId, chatId, args, token);
      return;
    case "/categories":
      await handleCategories(env, userId, chatId, args, token);
      return;
    case "/reminders":
      await handleToggle(env, userId, chatId, "reminders_enabled", args, "reminders", token);
      return;
    case "/digest":
      await handleToggle(env, userId, chatId, "digest_enabled", args, "digest", token);
      return;
    case "/mute":
      await setPreference(env.DB, userId, "muted", 1);
      await sendMessage(token, chatId, "Notifications muted. Use /unmute to resume.");
      return;
    case "/unmute":
      await setPreference(env.DB, userId, "muted", 0);
      await sendMessage(token, chatId, "Notifications unmuted.");
      return;
    case "/quiet":
      if (args.toLowerCase() === "off") {
        await setPreference(env.DB, userId, "quiet_start", null);
        await setPreference(env.DB, userId, "quiet_end", null);
        await sendMessage(token, chatId, "Quiet hours disabled.");
      } else {
        await handleQuiet(env, userId, chatId, args, token);
      }
      return;
    default:
      await sendMessage(token, chatId, "Unknown command. Use /help.");
  }
}



function verificationId(userId: string, messageId: number): string {
  return `verification:${userId}:${messageId}`;
}

async function storeVerificationText(
  env: Env,
  userId: string,
  chatId: number,
  messageId: number,
  text: string,
  forwarded: boolean,
): Promise<void> {
  const id = verificationId(userId, messageId);
  const now = new Date().toISOString();
  const {matches, conflictItemIds} = await findVerificationMatches(env.DB, now ? new Date(now) : new Date(), text);
  const strong = matches.filter((match) => match.score >= 0.35);
  const conflicting = strong.some((match) => conflictItemIds.has(match.item.id));
  const status = conflicting ? "CONFLICTING" : strong.length ? "MATCHED" : "UNVERIFIED";
  const summary = conflicting
    ? "Official information matching this submission is involved in a documented conflict; moderator review is required."
    : strong.length
      ? "Official verified information matches this submission."
      : "No sufficiently strong official match was found. This does not prove the submission false.";
  await env.DB.prepare(
    `INSERT OR IGNORE INTO verification_submissions
     (id,user_id,telegram_chat_id,telegram_message_id,intake_kind,submitted_text,status,result_summary,created_at,processed_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  ).bind(
    id, userId, String(chatId), messageId, forwarded ? "FORWARDED_TEXT" : "TEXT",
    text.slice(0, 10000), status, summary, now, now,
  ).run();
  for (const match of matches) {
    await env.DB.prepare(
      `INSERT OR REPLACE INTO verification_matches
       (submission_id,information_item_id,score,match_reason,matched_at)
       VALUES (?, ?, ?, ?, ?)`,
    ).bind(id, match.item.id, match.score, match.reason, now).run();
  }
  if (status !== "MATCHED") {
    await env.DB.prepare(
      `INSERT OR IGNORE INTO moderator_review_queue
       (id,submission_id,reason,status,created_at)
       VALUES (?, ?, ?, 'OPEN', ?)`,
    ).bind(
      `review:${id}`, id,
      conflicting ? "Conflicting official evidence." : "No strong deterministic official match.",
      now,
    ).run();
  }
  if (conflicting) {
    await sendMessage(env.TELEGRAM_BOT_TOKEN, chatId,
      "<b>Conflicting official evidence</b>\n\nI found official VGU information related to this submission, but the archive records a documented conflict. A moderator review is required; I will not choose a winner automatically.");
  } else if (strong.length) {
    await sendMessage(env.TELEGRAM_BOT_TOKEN, chatId,
      "<b>Official evidence match</b>\n\n" +
      strong.slice(0, 3).map((match, index) => formatInfo(match.item, index + 1)).join("\n\n"));
  } else {
    await sendMessage(env.TELEGRAM_BOT_TOKEN, chatId,
      "<b>Not officially confirmed.</b>\n\nNo sufficiently strong matching official VGU information was found in the current archive. This does not prove the submission false.");
  }
}

async function handleVerificationMedia(
  env: Env,
  userId: string,
  chatId: number,
  message: TelegramMessage,
): Promise<void> {
  const document = message.document;
  const photo = message.photo?.at(-1);
  const fileId = document?.file_id ?? photo?.file_id;
  if (!fileId) return;
  const mime = document?.mime_type ?? "image/jpeg";
  const size = document?.file_size ?? photo?.file_size ?? 0;
  if (size > 10 * 1024 * 1024) {
    await sendMessage(env.TELEGRAM_BOT_TOKEN, chatId, "That file is too large for verification. Please send a PDF/image up to 10 MiB.");
    return;
  }
  if (mime !== "application/pdf" && !mime.startsWith("image/")) {
    await sendMessage(env.TELEGRAM_BOT_TOKEN, chatId, "I can verify forwarded PDFs and images. Please send one of those file types.");
    return;
  }
  const id = verificationId(userId, message.message_id);
  const now = new Date().toISOString();
  const file = await getFile(env.TELEGRAM_BOT_TOKEN, fileId);
  if (!file.file_path) throw new Error("Telegram did not provide a downloadable file path");
  const body = await downloadFile(env.TELEGRAM_BOT_TOKEN, file.file_path);
  if (body.byteLength > 10 * 1024 * 1024) throw new Error("downloaded file exceeds verification limit");
  const safeName = (document?.file_name ?? (mime === "application/pdf" ? "submission.pdf" : "submission.jpg"))
    .replace(/[^A-Za-z0-9._-]/g, "_");
  const objectKey = `verification-submissions/${id}/${safeName}`;
  await env.EVIDENCE.put(objectKey, body, {
    httpMetadata: {contentType: mime},
    customMetadata: {userId, messageId: String(message.message_id)},
  });
  await env.DB.prepare(
    `INSERT OR IGNORE INTO verification_submissions
     (id,user_id,telegram_chat_id,telegram_message_id,intake_kind,content_type,file_name,object_key,submitted_text,status,created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'QUEUED', ?)`,
  ).bind(
    id, userId, String(chatId), message.message_id, mime === "application/pdf" ? "PDF" : "IMAGE",
    mime, safeName, objectKey, (message.caption ?? "").slice(0, 10000), now,
  ).run();
  await sendMessage(env.TELEGRAM_BOT_TOKEN, chatId,
    "<b>Verification received.</b>\n\nI saved the submitted image/PDF privately and will extract its text, compare it with verified official VGU evidence, and report either a match, a documented conflict, or <i>Not officially confirmed</i>. A missing match does not prove the claim false.");
}


async function handleUpdate(env: Env, update: TelegramUpdate): Promise<void> {
  const message = update.message;
  if (!message?.from) return;
  if (!privateChat(update)) {
    await sendMessage(env.TELEGRAM_BOT_TOKEN, message.chat.id, "Please use VGU Signal in a private chat.");
    return;
  }
  const user = await upsertUser(env.DB, message.from.id);
  const text = (message.text ?? "").trim();
  if (message.document || message.photo) {
    await handleVerificationMedia(env, user.id, message.chat.id, message);
    return;
  }
  if (!text.startsWith("/")) {
    if (message.forward_origin || message.forward_from) {
      await storeVerificationText(env, user.id, message.chat.id, message.message_id, text || message.caption || "", true);
      return;
    }
    if (await handleOnboarding(env, user.id, message.chat.id, text, env.TELEGRAM_BOT_TOKEN)) return;
    await sendMessage(env.TELEGRAM_BOT_TOKEN, message.chat.id, "Use /help to see available commands.");
    return;
  }
  if (await handleOnboarding(env, user.id, message.chat.id, text, env.TELEGRAM_BOT_TOKEN)) return;
  await handleCommand(env, user.id, message.chat.id, text, env.TELEGRAM_BOT_TOKEN);
}

interface NotificationUser {
  user_id: string;
  telegram_user_id: string;
  digest_enabled: number;
  reminders_enabled: number;
  muted: number;
  quiet_start: string | null;
  quiet_end: string | null;
}

async function notificationUsers(env: Env): Promise<NotificationUser[]> {
  const result = await env.DB.prepare(
    `SELECT u.id AS user_id, u.telegram_user_id, p.digest_enabled, p.reminders_enabled,
            p.muted, p.quiet_start, p.quiet_end
     FROM users u JOIN user_preferences p ON p.user_id = u.id
     WHERE u.status = 'ACTIVE'`,
  ).all<NotificationUser>();
  return result.results;
}

async function claimNotification(
  env: Env,
  userId: string,
  itemId: string,
  type: "REMINDER" | "WEEKLY_DIGEST",
  key: string,
): Promise<boolean> {
  const existing = await env.DB.prepare(
    `SELECT delivery_status FROM notifications
     WHERE user_id = ? AND information_item_id = ? AND notification_type = ? AND scheduled_key = ?`,
  ).bind(userId, itemId, type, key).first<{delivery_status: string}>();
  if (existing?.delivery_status === "SENT") return false;
  if (existing?.delivery_status === "PENDING") return false;

  const id = `notification:${userId}:${type}:${itemId}:${key}`;
  await env.DB.prepare(
    `INSERT INTO notifications(id, user_id, information_item_id, notification_type,
       scheduled_key, created_at, delivery_status)
     VALUES (?, ?, ?, ?, ?, ?, 'PENDING')
     ON CONFLICT(user_id, information_item_id, notification_type, scheduled_key)
     DO UPDATE SET delivery_status = 'PENDING', created_at = excluded.created_at`,
  ).bind(id, userId, itemId, type, key, new Date().toISOString()).run();
  return true;
}

async function markNotification(
  env: Env,
  userId: string,
  itemId: string,
  type: "REMINDER" | "WEEKLY_DIGEST",
  key: string,
  status: "SENT" | "FAILED",
): Promise<void> {
  await env.DB.prepare(
    `UPDATE notifications SET delivery_status = ?, delivered_at = ?
     WHERE user_id = ? AND information_item_id = ? AND notification_type = ? AND scheduled_key = ?`,
  ).bind(status, new Date().toISOString(), userId, itemId, type, key).run();
}

async function runReminders(env: Env, now: Date): Promise<void> {
  for (const user of await notificationUsers(env)) {
    if (!user.reminders_enabled || user.muted || matchesQuietHours(now, user.quiet_start, user.quiet_end)) continue;
    const preferences = await getPreferences(env.DB, user.user_id);
    if (!preferences) continue;
    for (const item of await getUpcoming(env.DB, preferences, now, 1, 5)) {
      if (!item.due_at) continue;
      const due = new Date(item.due_at);
      if (due <= now || due.getTime() > now.getTime() + 86400000) continue;
      const key = due.toISOString().slice(0, 13);
      if (!await claimNotification(env, user.user_id, item.id, "REMINDER", key)) continue;
      try {
        await sendMessage(env.TELEGRAM_BOT_TOKEN, Number(user.telegram_user_id), `<b>Deadline reminder</b>\n\n${formatInfo(item)}`);
        await markNotification(env, user.user_id, item.id, "REMINDER", key, "SENT");
      } catch {
        await markNotification(env, user.user_id, item.id, "REMINDER", key, "FAILED");
      }
    }
  }
}

async function runWeeklyDigest(env: Env, now: Date): Promise<void> {
  const key = isoWeekKey(now);
  for (const user of await notificationUsers(env)) {
    if (!user.digest_enabled || user.muted || matchesQuietHours(now, user.quiet_start, user.quiet_end)) continue;
    const preferences = await getPreferences(env.DB, user.user_id);
    if (!preferences) continue;
    const items = await getUpcoming(env.DB, preferences, now, 7, 10);
    if (!items.length) continue;
    const itemId = "__WEEKLY_DIGEST__";
    if (!await claimNotification(env, user.user_id, itemId, "WEEKLY_DIGEST", key)) continue;
    try {
      await sendMessage(env.TELEGRAM_BOT_TOKEN, Number(user.telegram_user_id), formatList("Your weekly VGU Signal digest", items));
      await markNotification(env, user.user_id, itemId, "WEEKLY_DIGEST", key, "SENT");
    } catch {
      await markNotification(env, user.user_id, itemId, "WEEKLY_DIGEST", key, "FAILED");
    }
  }
}

function isoWeekKey(date: Date): string {
  const day = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
  const weekday = day.getUTCDay() || 7;
  day.setUTCDate(day.getUTCDate() + 4 - weekday);
  const yearStart = new Date(Date.UTC(day.getUTCFullYear(), 0, 1));
  const week = Math.ceil((((day.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
  return `${day.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "GET") {
      const dbCheck = await env.DB.prepare("SELECT 1 AS ok").first<{ok: number}>().catch(() => null);
      const r2Check = await env.EVIDENCE.list({limit: 1}).then(() => true).catch(() => false);
      return Response.json({
        service: "vgu-signal-worker",
        status: dbCheck?.ok === 1 && r2Check ? "ok" : "degraded",
        phase: 6,
        dependencies: {d1: dbCheck?.ok === 1, r2: r2Check},
      }, {status: dbCheck?.ok === 1 && r2Check ? 200 : 503});
    }
    if (request.method !== "POST") return new Response("Method Not Allowed", {status: 405});
    if (env.TELEGRAM_WEBHOOK_SECRET) {
      const provided = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
      if (provided !== env.TELEGRAM_WEBHOOK_SECRET) return new Response("Unauthorized", {status: 401});
    }
    try {
      await handleUpdate(env, (await request.json()) as TelegramUpdate);
      return new Response("ok");
    } catch {
      return new Response("Bad request", {status: 500});
    }
  },

  async scheduled(_event: ScheduledEvent, env: Env): Promise<void> {
    const now = new Date();
    await runReminders(env, now);
    if (now.getUTCDay() === 1 && now.getUTCHours() === 3 && now.getUTCMinutes() < 15) {
      await runWeeklyDigest(env, now);
    }
  },
};
