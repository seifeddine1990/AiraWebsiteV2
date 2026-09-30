(function () {
  "use strict";
  var config = window.AIRA_CONFIG;
  var host = document.getElementById("aira-chat");
  if (!host || !config || !config.enabled) return;
  var root = host.dataset.root || "";
  var faqs = window.AIRA_FAQS || [];
  var transcript = [];
  var pending = false;
  function normalize(text) {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  }
  function matchQuestion(text) {
    var normalized = " " + normalize(text) + " ";
    var best = null, score = 0;
    faqs.forEach(function (faq) {
      var matches = faq.keywords.reduce(function (sum, term) {
        return sum + (normalized.includes(" " + normalize(term) + " ") ? normalize(term).length : 0);
      }, 0);
      if (matches > score) { best = faq; score = matches; }
    });
    return best;
  }
  host.innerHTML = `
    <button class="aira-launch" type="button" aria-expanded="false" aria-controls="aira-panel">
      <img class="aira-avatar" alt="" width="56" height="56"><span>Ask AIRA</span>
    </button>
    <section id="aira-panel" class="aira-panel" role="dialog" aria-labelledby="aira-title" hidden>
      <header class="aira-header"><div class="aira-identity"><img class="aira-header-avatar" alt="" width="56" height="56"><div><strong id="aira-title">Ask AIRA</strong><small>Website guide · Prepared answers</small></div></div><button type="button" class="aira-close" aria-label="Close chat">×</button></header>
      <div class="aira-body">
        <div class="aira-messages" role="log" aria-label="Conversation" aria-live="polite" aria-relevant="additions"></div>
        <div class="aira-topics" aria-label="Suggested topics"></div>
        <form class="aira-question"><label for="aira-question">Your question</label><div class="aira-input-row"><input id="aira-question" name="question" maxlength="300" required placeholder="e.g. deployment options" autocomplete="off"><button type="submit">Ask</button></div></form>
        <button class="aira-contact" type="button" aria-expanded="false" aria-controls="aira-lead">Contact our team</button>
        <form id="aira-lead" class="aira-lead" hidden>
          <label for="aira-name">Name</label><input id="aira-name" name="name" autocomplete="name" maxlength="100" required>
          <label for="aira-email">Email</label><input id="aira-email" name="email" type="email" autocomplete="email" maxlength="254" required>
          <label for="aira-company">Company (optional)</label><input id="aira-company" name="company" autocomplete="organization" maxlength="150">
          <label for="aira-message">How can we help?</label><textarea id="aira-message" name="message" rows="3" maxlength="3000" required></textarea>
          <div class="aira-trap" aria-hidden="true"><label for="aira-website">Leave this field empty</label><input id="aira-website" name="_honey" tabindex="-1" autocomplete="off"></div>
          <label class="aira-check"><input name="includeTranscript" type="checkbox"> Include this conversation with my request</label>
          <p class="aira-note">Your details and any included conversation will be sent to AIRA Fusion through FormSubmit. Please avoid sensitive information.</p>
          <button class="aira-send" type="submit">Send request</button>
          <p class="aira-status" role="status" aria-live="polite"></p>
        </form>
        <a class="aira-contact-link">Visit our contact page ↗</a>
      </div>
    </section>`;
  var launcher = host.querySelector(".aira-launch");
  var panel = host.querySelector(".aira-panel");
  var messages = host.querySelector(".aira-messages");
  var question = host.querySelector(".aira-question");
  var input = question.elements.question;
  var lead = host.querySelector(".aira-lead");
  var status = host.querySelector(".aira-status");
  var send = host.querySelector(".aira-send");
  var contact = host.querySelector(".aira-contact");
  var headerAvatar = host.querySelector(".aira-header-avatar");
  var replyAnimation;
  host.querySelectorAll(".aira-avatar, .aira-header-avatar").forEach(function (avatar) {
    avatar.addEventListener("error", function () { avatar.hidden = true; });
    avatar.src = root + config.avatar;
  });
  host.querySelector(".aira-contact-link").href = root + "contact.html";
  function addMessage(speaker, text, page) {
    var message = document.createElement("div");
    message.className = "aira-message" + (speaker === "You" ? " aira-user" : "");
    var label = document.createElement("strong");
    label.textContent = speaker;
    var content = document.createElement("p");
    content.textContent = text;
    message.append(label, content);
    // Only local HTML pages from the editable FAQ configuration are linked.
    if (page && /^[a-z0-9/_-]+\.html(?:#[a-z0-9_-]+)?$/i.test(page)) {
      var link = document.createElement("a");
      link.href = root + page;
      link.textContent = "Read more ↗";
      message.append(link);
    }
    messages.append(message);
    transcript.push(speaker + ": " + text);
    if (transcript.length > 60) { transcript.shift(); messages.firstElementChild.remove(); }
    message.scrollIntoView({ block: "nearest" });
  }
  function answer(text, faq) {
    addMessage("You", text);
    addMessage("AIRA", faq ? faq.answer : "I couldn’t match that to a prepared answer. Choose a topic below, or contact our team for help.", faq && faq.page);
    if (headerAvatar.animate && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      if (replyAnimation) replyAnimation.cancel();
      replyAnimation = headerAvatar.animate([
        { transform: "scale(1)", filter: "brightness(1)" },
        { transform: "scale(1.08)", filter: "brightness(1.2)" },
        { transform: "scale(1)", filter: "brightness(1)" }
      ], { duration: 650, iterations: 2, easing: "ease-in-out" });
    }
  }
  faqs.forEach(function (faq) {
    var button = document.createElement("button");
    button.type = "button";
    button.textContent = faq.label;
    button.addEventListener("click", function () { answer(faq.label, faq); });
    host.querySelector(".aira-topics").append(button);
  });
  function setOpen(open) {
    panel.hidden = !open;
    launcher.setAttribute("aria-expanded", String(open));
    if (open) { input.focus({ preventScroll: true }); } else { launcher.focus(); }
  }
  launcher.addEventListener("click", function () { setOpen(panel.hidden); });
  host.querySelector(".aira-close").addEventListener("click", function () { setOpen(false); });
  host.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !panel.hidden) { event.preventDefault(); setOpen(false); }
  });
  question.addEventListener("submit", function (event) {
    event.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    answer(text, matchQuestion(text));
    input.value = "";
    input.focus({ preventScroll: true });
  });
  contact.addEventListener("click", function () {
    lead.hidden = !lead.hidden;
    contact.setAttribute("aria-expanded", String(!lead.hidden));
    if (!lead.hidden) lead.elements.name.focus();
  });
  lead.addEventListener("submit", async function (event) {
    event.preventDefault();
    if (pending || !lead.reportValidity()) return;
    if (lead.elements._honey.value) return;
    var payload = {
      name: lead.elements.name.value.trim(),
      email: lead.elements.email.value.trim(),
      company: lead.elements.company.value.trim(),
      message: lead.elements.message.value.trim(),
      source: "Ask AIRA",
      _honey: "",
      page: location.origin + location.pathname
    };
    if (!payload.name || !payload.message) {
      status.textContent = "Please enter your name and message.";
      return;
    }
    if (lead.elements.includeTranscript.checked) payload.conversation = transcript.join("\n\n");
    pending = true;
    send.disabled = true;
    send.textContent = "Sending…";
    status.textContent = "";
    try {
      await window.AIRA_EMAIL.send(payload);
      status.textContent = "Your request has been accepted for delivery. Thank you for contacting AIRA Fusion.";
      lead.reset();
    } catch (error) {
      status.textContent = error.code === "NOT_CONFIGURED"
        ? "Chat enquiries are not available yet. Please use the contact page below."
        : "We couldn’t confirm delivery. Your details are still here. Try again or use the contact page below.";
    } finally {
      pending = false;
      send.disabled = false;
      send.textContent = "Send request";
    }
  });
  host.hidden = false;
  addMessage("AIRA", config.greeting);
})();
