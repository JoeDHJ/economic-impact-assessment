"use strict";
importScripts("vendor/highs.js", "workforce-core.js");
let solver;
self.onmessage = async ({ data }) => {
  try {
    Workforce.validate(data.workspace, data.template, data.model);
    self.postMessage({ type: "progress", message: "Loading local solver…" });
    solver =
      solver ||
      (await Module({
        locateFile: (f) => new URL("vendor/" + f, self.location.href).href,
      }));
    let results = [];
    const variants = data.compare
      ? Workforce.variants(data.workspace)
      : [[data.workspace, null]];
    for (let i = 0; i < variants.length; i++) {
      self.postMessage({
        type: "progress",
        message: `Solving option ${i + 1} of ${variants.length}…`,
      });
      const result = Workforce.run(
        variants[i][0],
        data.model,
        solver,
        variants[i][1],
      );
      if (data.compare)
        result.option = [
          "No workforce programme",
          "Hire and contract only",
          "Mixed workforce plan",
          variants[3][0].name,
        ][i];
      results.push(result);
    }
    self.postMessage({
      type: "result",
      results,
      comparison: Workforce.comparison(results),
      compare: data.compare,
    });
  } catch (e) {
    self.postMessage({ type: "error", message: e.message || String(e) });
  }
};
