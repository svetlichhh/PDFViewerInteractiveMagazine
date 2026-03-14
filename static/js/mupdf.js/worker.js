"use strict"

import * as mupdf from "./node_modules/mupdf/dist/mupdf.js"

for (var name in mupdf) {
    console.log(`mupdf.${name}=${mupdf[name]}`)
}