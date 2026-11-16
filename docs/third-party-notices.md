# Third-party solver notices

The browser includes **highs-js 1.15.4**, from the npm `highs` package and [lovasoa/highs-js](https://github.com/lovasoa/highs-js). Its distributed `build/highs.js` and `build/highs.wasm` are vendored unchanged. Source package retrieved 16 November 2026. The wrapper is MIT licensed; its notice is retained as `web/vendor/highs-js-LICENSE.txt` in source and installed distributions.

HiGHS is MIT licensed by its contributors. The [upstream license](https://github.com/ERGO-Code/HiGHS/blob/master/LICENSE.txt) is included as `web/vendor/HiGHS-LICENSE.txt`. The bundled compiled solver is provided by the pinned highs-js release. Python uses the separately installed SciPy/HiGHS integration; Python package versions are recorded by the active environment, not inferred from the browser version.

No CDN, remote solver service or API key is used. Browser WebAssembly loading requires an HTTP origin such as the supplied loopback server or GitHub Pages. Published default results and the original regional calculator remain readable through a local file URL.
