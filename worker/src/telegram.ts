export interface TelegramUser {
  id: number;
  first_name?: string;
  username?: string;
}

export interface TelegramChat {
  id: number;
  type: string;
}

export interface TelegramFile {
  file_id: string;
  file_unique_id: string;
  file_size?: number;
  file_path?: string;
}

export interface TelegramPhotoSize {
  file_id: string;
  file_unique_id: string;
  width: number;
  height: number;
  file_size?: number;
}

export interface TelegramDocument {
  file_id: string;
  file_unique_id: string;
  file_name?: string;
  mime_type?: string;
  file_size?: number;
}

export interface TelegramMessage {
  message_id: number;
  chat: TelegramChat;
  from?: TelegramUser;
  text?: string;
  caption?: string;
  document?: TelegramDocument;
  photo?: TelegramPhotoSize[];
  forward_origin?: unknown;
  forward_from?: TelegramUser;
  forward_date?: number;
}

export interface TelegramUpdate {
  update_id: number;
  message?: TelegramMessage;
}

interface TelegramResponse<T> {
  ok: boolean;
  result?: T;
  description?: string;
}

export async function telegramRequest<T>(
  token: string,
  method: string,
  payload: Record<string, unknown>,
): Promise<T> {
  const response = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
    method: "POST",
    headers: {"content-type": "application/json"},
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Telegram HTTP error: ${response.status}`);
  }
  const result = (await response.json()) as TelegramResponse<T>;
  if (!result.ok || result.result === undefined) {
    throw new Error(result.description ?? "Telegram API request failed");
  }
  return result.result;
}

export function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export async function sendMessage(
  token: string,
  chatId: number,
  text: string,
): Promise<void> {
  await telegramRequest(token, "sendMessage", {
    chat_id: chatId,
    text,
    parse_mode: "HTML",
    disable_web_page_preview: true,
  });
}

export async function setWebhook(
  token: string,
  url: string,
  secretToken?: string,
): Promise<void> {
  await telegramRequest(token, "setWebhook", {
    url,
    secret_token: secretToken,
    allowed_updates: ["message"],
    drop_pending_updates: false,
  });
}


export async function getFile(token: string, fileId: string): Promise<TelegramFile> {
  return telegramRequest<TelegramFile>(token, "getFile", {file_id: fileId});
}

export async function downloadFile(token: string, filePath: string): Promise<ArrayBuffer> {
  const response = await fetch(`https://api.telegram.org/file/bot${token}/${filePath}`);
  if (!response.ok) throw new Error(`Telegram file download failed: ${response.status}`);
  return response.arrayBuffer();
}
