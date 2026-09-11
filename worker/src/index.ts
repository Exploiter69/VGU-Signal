export interface Env {
  DB: D1Database;
}

export default {
  async fetch(request: Request, _env: Env): Promise<Response> {
    if (request.method !== "GET") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    return Response.json({
      service: "vgu-signal-worker",
      status: "ok",
    });
  },
};
