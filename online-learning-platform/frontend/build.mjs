// Builds the React app with esbuild.
//   npm run dev    -> development server on http://localhost:5173
//   npm run build  -> optimised files in dist/
import * as esbuild from "esbuild";
import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { createServer, request } from "node:http";

const serve = process.argv.includes("--serve");

// Read API_URL from the environment, or from frontend/.env for local work.
async function apiUrl() {
  if (process.env.API_URL !== undefined) return process.env.API_URL;
  if (existsSync(".env")) {
    const match = (await readFile(".env", "utf8")).match(/^\s*API_URL\s*=\s*(.*)$/m);
    if (match) return match[1].trim().replace(/^["']|["']$/g, "");
  }
  return serve ? "http://localhost:5000" : "";
}

const API_URL = (await apiUrl()).replace(/\/+$/, "");
if (process.env.VERCEL && !API_URL) {
  console.error("Set the API_URL environment variable to your backend address, then redeploy.");
  process.exit(1);
}

await rm("dist", { recursive: true, force: true });
await mkdir("dist/assets", { recursive: true });
await cp("public", "dist", { recursive: true });

// Production file names carry a content hash so browsers never run stale code.
const options = {
  entryPoints: ["src/main.jsx", "src/styles.css"],
  bundle: true,
  outdir: "dist/assets",
  entryNames: serve ? "[name]" : "[name]-[hash]",
  format: "esm",
  jsx: "automatic",
  target: ["es2020"],
  minify: !serve,
  sourcemap: serve,
  metafile: true,
  define: {
    __API_URL__: JSON.stringify(API_URL),
    "process.env.NODE_ENV": JSON.stringify(serve ? "development" : "production"),
  },
  logLevel: "info",
};

async function writeHtml(metafile) {
  const outputs = Object.keys(metafile.outputs);
  const asset = (pattern) => "/" + outputs.find((f) => pattern.test(f)).replace(/^dist\//, "");
  const html = (await readFile("public/index.html", "utf8"))
    .replace("%JS%", asset(/main(-\w+)?\.js$/))
    .replace("%CSS%", asset(/styles(-\w+)?\.css$/));
  await writeFile("dist/index.html", html);
}

if (!serve) {
  const result = await esbuild.build(options);
  await writeHtml(result.metafile);
  console.log(`Built dist/ (API address: ${API_URL || "same origin"})`);
} else {
  const context = await esbuild.context({
    ...options,
    plugins: [{ name: "html", setup: (b) => b.onEnd((r) => r.metafile && writeHtml(r.metafile)) }],
  });
  await context.watch();
  const inner = await context.serve({ servedir: "dist", host: "127.0.0.1", port: 5174 });
  // A small proxy so that reloading a page such as /courses/3 returns index.html.
  createServer((incoming, outgoing) => {
    const pathname = incoming.url.split("?")[0];
    const path = /\.[a-z0-9]+$/i.test(pathname) ? incoming.url : "/index.html";
    const proxy = request(
      { host: "127.0.0.1", port: inner.port, path, method: incoming.method, headers: incoming.headers },
      (reply) => {
        outgoing.writeHead(reply.statusCode, reply.headers);
        reply.pipe(outgoing);
      }
    );
    proxy.on("error", () => outgoing.writeHead(502).end("Build server unavailable"));
    incoming.pipe(proxy);
  }).listen(5173, () => console.log(`\nOpen http://localhost:5173  (API: ${API_URL})`));
}
