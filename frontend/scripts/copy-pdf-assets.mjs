import { cpSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";

const packageRoot = new URL("../node_modules/pdfjs-dist/", import.meta.url);
const output = new URL("../public/pdfjs/", import.meta.url);
mkdirSync(output, { recursive: true });
for (const directory of ["cmaps", "standard_fonts", "wasm"]) {
  cpSync(fileURLToPath(new URL(directory, packageRoot)), fileURLToPath(new URL(directory, output)), { recursive: true });
}
cpSync(fileURLToPath(new URL("LICENSE", packageRoot)), fileURLToPath(new URL("LICENSE", output)));
