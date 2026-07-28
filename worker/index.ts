interface Env {
	ASSETS?: Fetcher;
	// 浏览量计数器 KV 命名空间
	PAGE_VIEWS: KVNamespace;
}

export default {
	async fetch(request, env, ctx): Promise<Response> {
		const url = new URL(request.url);
		const corsHeaders = {
			"Access-Control-Allow-Origin": "*",
			"Access-Control-Allow-Methods": "GET, POST, OPTIONS",
			"Access-Control-Allow-Headers": "Content-Type",
		};

		if (request.method === "OPTIONS") {
			return new Response(null, { headers: corsHeaders });
		}

		// ============ 浏览量计数器 API ============
		// POST /api/views/hit?slug=xxx  增加一次浏览量（同一会话内只计一次）
		// GET  /api/views/get?slug=xxx  获取当前浏览量
		if (url.pathname === "/api/views/hit" && request.method === "POST") {
			return handleViewHit(request, env, url, corsHeaders);
		}
		if (url.pathname === "/api/views/get" && request.method === "GET") {
			return handleViewGet(request, env, url, corsHeaders);
		}

		// ============ 图片搜索 API（保留） ============
		if (url.pathname === "/api/image-search" && request.method === "POST") {
			try {
				const formData = await request.formData();
				const file = formData.get("file");

				if (!file || !(file instanceof File)) {
					return new Response(JSON.stringify({ error: "请上传图片文件" }), {
						status: 400,
						headers: { "Content-Type": "application/json", ...corsHeaders },
					});
				}

				const imageUrl = await uploadImage(file);

				return new Response(JSON.stringify({ url: imageUrl }), {
					headers: { "Content-Type": "application/json", ...corsHeaders },
				});
			} catch (error) {
				console.error("Image search error:", error);
				return new Response(
					JSON.stringify({
						error: error instanceof Error ? error.message : "图片上传失败",
					}),
					{
						status: 500,
						headers: { "Content-Type": "application/json", ...corsHeaders },
					},
				);
			}
		}

		if (env.ASSETS) {
			return env.ASSETS.fetch(request);
		}

		return new Response("Not Found", { status: 404 });
	},
} satisfies ExportedHandler<Env>;

// 浏览量 KV key 前缀
const VIEW_KEY_PREFIX = "view:";
// 会话去重 key 前缀（30 分钟内同一 slug 不重复计数）
const SESSION_KEY_PREFIX = "session:";
// 会话去重时长（秒）
const SESSION_TTL = 30 * 60;
// KV 写后异步广播更新最近浏览量（可选，简化实现暂不启用）

// 获取客户端 IP（Cloudflare 提供）
function getClientIp(request: Request): string {
	const cfIp = request.headers.get("cf-connecting-ip");
	if (cfIp) return cfIp;
	const xRealIp = request.headers.get("x-real-ip");
	if (xRealIp) return xRealIp;
	return "unknown";
}

async function handleViewHit(
	request: Request,
	env: Env,
	url: URL,
	corsHeaders: Record<string, string>,
): Promise<Response> {
	try {
		const slug = url.searchParams.get("slug");
		if (!slug) {
			return jsonResponse({ error: "missing slug" }, 400, corsHeaders);
		}
		if (slug.length > 200 || /[:\s]/.test(slug)) {
			return jsonResponse({ error: "invalid slug" }, 400, corsHeaders);
		}

		const ip = getClientIp(request);
		const sessionKey = `${SESSION_KEY_PREFIX}${slug}:${ip}`;
		const existed = await env.PAGE_VIEWS.get(sessionKey);
		if (existed) {
			const current = await env.PAGE_VIEWS.get(`${VIEW_KEY_PREFIX}${slug}`);
			return jsonResponse({ slug, views: Number(current) || 0, counted: false }, 200, corsHeaders);
		}

		await env.PAGE_VIEWS.put(sessionKey, "1", { expirationTtl: SESSION_TTL });

		const viewKey = `${VIEW_KEY_PREFIX}${slug}`;
		const current = Number((await env.PAGE_VIEWS.get(viewKey)) || 0);
		const next = current + 1;
		await env.PAGE_VIEWS.put(viewKey, String(next));

		return jsonResponse({ slug, views: next, counted: true }, 200, corsHeaders);
	} catch (e: unknown) {
		const msg = e instanceof Error ? e.message : String(e);
		return jsonResponse({ error: "hit failed", detail: msg }, 500, corsHeaders);
	}
}

async function handleViewGet(
	_request: Request,
	env: Env,
	url: URL,
	corsHeaders: Record<string, string>,
): Promise<Response> {
	const slug = url.searchParams.get("slug");
	if (!slug) {
		return jsonResponse({ error: "missing slug" }, 400, corsHeaders);
	}
	if (!slug || slug.length > 200 || /[:\s]/.test(slug)) {
		return jsonResponse({ error: "invalid slug" }, 400, corsHeaders);
	}
	const current = Number((await env.PAGE_VIEWS.get(`${VIEW_KEY_PREFIX}${slug}`)) || 0);
	return jsonResponse({ slug, views: current }, 200, corsHeaders);
}

function jsonResponse(
	body: unknown,
	status: number,
	corsHeaders: Record<string, string>,
): Response {
	return new Response(JSON.stringify(body), {
		status,
		headers: { "Content-Type": "application/json", ...corsHeaders },
	});
}

async function uploadImage(file: File): Promise<string> {
	const fileWithType = new File([await file.arrayBuffer()], file.name, {
		type: file.type || "image/png",
	});
	let lastError: Error | null = null;

	// 方案1：Telegraph 图床
	try {
		const uploadFormData = new FormData();
		uploadFormData.append("file", fileWithType);

		const response = await fetch("https://telegra.ph/upload", {
			method: "POST",
			body: uploadFormData,
		});

		if (response.ok) {
			const data = (await response.json()) as Array<{ src: string }>;
			if (Array.isArray(data) && data[0]?.src) {
				return `https://telegra.ph${data[0].src}`;
			}
		}
	} catch (error) {
		lastError = error instanceof Error ? error : new Error("Telegraph 上传失败");
	}

	// 方案2：0x0.st 图床
	try {
		const uploadFormData = new FormData();
		uploadFormData.append("file", fileWithType);

		const response = await fetch("https://0x0.st", {
			method: "POST",
			body: uploadFormData,
		});

		if (response.ok) {
			const text = (await response.text()).trim();
			if (text && text.startsWith("http")) {
				return text;
			}
		}
	} catch (error) {
		lastError = error instanceof Error ? error : new Error("0x0.st 上传失败");
	}

	throw lastError || new Error("所有图床上传均失败");
}
