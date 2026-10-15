(function () {
  "use strict";
  var form = document.querySelector("form[data-aira-contact]");
  if (!form || !window.AIRA_EMAIL) return;
  var button = form.querySelector('button[type="submit"]');
  var status = form.querySelector(".form-ok");
  var pending = false;
  button.disabled = false;
  // The interactive tools link here with ?topic=…&brief=… to pre-fill the enquiry.
  var params = new URLSearchParams(location.search);
  var brief = params.get("brief");
  var topic = params.get("topic");
  if (brief && !form.elements.message.value) form.elements.message.value = brief.slice(0, 4000);
  if (topic) Array.prototype.forEach.call(form.elements.topic.options, function (o) { if (o.text === topic) o.selected = true; });
  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    if (pending || !form.reportValidity() || form.elements._honey.value) return;
    var fields = {};
    ["name", "role", "company", "email", "topic", "message"].forEach(function (key) {
      fields[key] = form.elements[key].value.trim();
    });
    status.classList.add("show");
    if (!fields.name || !fields.company) {
      status.textContent = "Please enter your name and organisation.";
      return;
    }
    fields.source = "Contact Us";
    fields.page = location.origin + location.pathname;
    fields._honey = "";
    pending = true;
    button.disabled = true;
    button.textContent = "Sending…";
    status.textContent = "";
    try {
      await window.AIRA_EMAIL.send(fields);
      status.textContent = "Your request has been accepted for delivery. Thank you for contacting AIRA Fusion.";
      form.reset();
    } catch (error) {
      status.textContent = error.code === "NOT_CONFIGURED"
        ? "Online enquiries are not available yet. Please use the direct email link on this page."
        : "We couldn’t confirm delivery. Your details are still here. Try again or use the direct email link on this page.";
    } finally {
      pending = false;
      button.disabled = false;
      button.textContent = "Send request";
    }
  });
})();
