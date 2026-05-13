(function () {
  var timings = (window.__elbysodicHtmxTimings = window.__elbysodicHtmxTimings || []);

  function pathFor(event) {
    var detail = event.detail || {};
    var requestConfig = detail.requestConfig || {};
    return requestConfig.path || requestConfig.url || window.location.pathname;
  }

  document.body.addEventListener("htmx:beforeRequest", function (event) {
    event.detail.__elbysodicStartedAt = performance.now();
  });

  document.body.addEventListener("htmx:afterRequest", function (event) {
    var detail = event.detail || {};
    var startedAt = detail.__elbysodicStartedAt;
    if (typeof startedAt !== "number") {
      return;
    }
    var duration = Math.round((performance.now() - startedAt) * 10) / 10;
    var entry = {
      path: pathFor(event),
      durationMs: duration,
      status: detail.xhr ? detail.xhr.status : 0,
      boosted: Boolean(detail.boosted),
      timestamp: new Date().toISOString()
    };
    timings.push(entry);
    if (window.console && window.console.debug) {
      window.console.debug("[elbysodic] htmx", entry);
    }
  });
})();
