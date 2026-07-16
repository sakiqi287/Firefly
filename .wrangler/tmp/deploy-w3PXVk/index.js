var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// worker/index.ts
var index_default = {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    };
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }
    if (url.pathname === "/api/image-search" && request.method === "POST") {
      try {
        const formData = await request.formData();
        const file = formData.get("file");
        if (!file || !(file instanceof File)) {
          return new Response(JSON.stringify({ error: "\u8BF7\u4E0A\u4F20\u56FE\u7247\u6587\u4EF6" }), {
            status: 400,
            headers: { "Content-Type": "application/json", ...corsHeaders }
          });
        }
        const imageUrl = await uploadImage(file);
        return new Response(JSON.stringify({ url: imageUrl }), {
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      } catch (error) {
        console.error("Image search error:", error);
        return new Response(
          JSON.stringify({
            error: error instanceof Error ? error.message : "\u56FE\u7247\u4E0A\u4F20\u5931\u8D25"
          }),
          {
            status: 500,
            headers: { "Content-Type": "application/json", ...corsHeaders }
          }
        );
      }
    }
    return env.ASSETS.fetch(request);
  }
};
async function uploadImage(file) {
  let lastError = null;
  try {
    const uploadFormData = new FormData();
    uploadFormData.append("file", file);
    const response = await fetch("https://telegra.ph/upload", {
      method: "POST",
      body: uploadFormData
    });
    if (response.ok) {
      const data = await response.json();
      if (Array.isArray(data) && data[0]?.src) {
        return `https://telegra.ph${data[0].src}`;
      }
    }
  } catch (error) {
    lastError = error instanceof Error ? error : new Error("Telegraph \u4E0A\u4F20\u5931\u8D25");
  }
  try {
    const uploadFormData = new FormData();
    uploadFormData.append("file", file);
    const response = await fetch("https://0x0.st", {
      method: "POST",
      body: uploadFormData
    });
    if (response.ok) {
      const text = (await response.text()).trim();
      if (text && text.startsWith("http")) {
        return text;
      }
    }
  } catch (error) {
    lastError = error instanceof Error ? error : new Error("0x0.st \u4E0A\u4F20\u5931\u8D25");
  }
  throw lastError || new Error("\u6240\u6709\u56FE\u5E8A\u4E0A\u4F20\u5747\u5931\u8D25");
}
__name(uploadImage, "uploadImage");
export {
  index_default as default
};
//# sourceMappingURL=index.js.map
