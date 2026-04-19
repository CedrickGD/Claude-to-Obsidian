#!/usr/bin/env node
import { readFileSync, writeFileSync } from "node:fs";
import { Resvg } from "@resvg/resvg-js";

const [, , inputPath = "src-tauri/icons/source.svg", outputPath = "src-tauri/icons/source.png", sizeArg = "1024"] = process.argv;

const svg = readFileSync(inputPath);
const size = parseInt(sizeArg, 10);
const resvg = new Resvg(svg, {
  fitTo: { mode: "width", value: size },
  background: "rgba(0,0,0,0)",
});
const png = resvg.render().asPng();
writeFileSync(outputPath, png);
console.log(`Rasterized ${inputPath} → ${outputPath} (${size}x${size})`);
