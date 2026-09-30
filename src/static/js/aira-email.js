// Shared delivery for Contact Us and Ask AIRA. No mailbox credentials are needed.
(function () {
  "use strict";
  window.AIRA_EMAIL = {
    send: async function (fields) {
      var config = window.AIRA_CONFIG || {};
      var recipient = (config.recipient || "").trim();
      if (!recipient || /[\s/?#]/.test(recipient)) {
        var error = new Error("Email enquiries are not configured");
        error.code = "NOT_CONFIGURED";
        throw error;
      }
      var controller = new AbortController();
      var timer = setTimeout(function () { controller.abort(); }, 20000);
      try {
        var response = await fetch("https://formsubmit.co/ajax/" + encodeURIComponent(recipient), {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify(Object.assign({}, fields, {
            _subject: config.emailSubject || "AIRA website enquiry",
            _template: "table"
          })),
          signal: controller.signal
        });
        var result = await response.json();
        if (!response.ok || (result.success !== true && result.success !== "true")) throw new Error("Submission rejected");
      } finally { clearTimeout(timer); }
    }
  };
})();
