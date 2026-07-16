interface Env {
	ASSETS: Fetcher;
}

export default {
	async fetch(request, env, ctx): Promise<Response> {
		const url = new URL(request.url);
		const corsHeaders = {
			"Access-Control-Allow-Origin": "*",
			"Access-Control-Allow-Methods": "POST, OPTIONS",
			"Access-Control-Allow-Headers": "Content-Type",
		};

		if (request.method === "OPTIONS") {
			return new Response(null, { headers: corsHeaders });
		}

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

		return env.ASSETS.fetch(request);
	},
} satisfies ExportedHandler<Env>;

async function uploadImage(file: File): Promise<string> {
	let lastError: Error | null = null;

	// 方案1：Telegraph 图床
	try {
		const uploadFormData = new FormData();
		uploadFormData.append("file", file);

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
		uploadFormData.append("file", file);

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
