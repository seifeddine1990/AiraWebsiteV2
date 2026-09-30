# Requires a local preview at :8091 and Edge/Chrome remote debugging at :9223.
# All email requests are mocked: this check never contacts FormSubmit.
param([int]$DebugPort = 9223)
$ErrorActionPreference = 'Stop'
$tab = Invoke-RestMethod "http://localhost:$DebugPort/json/list" | ForEach-Object { $_ } | Where-Object { $_.type -eq 'page' } | Select-Object -First 1
$ws = [System.Net.WebSockets.ClientWebSocket]::new()
$ct = [System.Threading.CancellationToken]::None
$ws.ConnectAsync([uri]$tab.webSocketDebuggerUrl, $ct).GetAwaiter().GetResult() | Out-Null
$script:seq = 0
function Cdp($method, $params) {
  $script:seq++
  $id = $script:seq
  $bytes = [Text.Encoding]::UTF8.GetBytes((@{id=$id;method=$method;params=$params} | ConvertTo-Json -Depth 30 -Compress))
  $ws.SendAsync([ArraySegment[byte]]::new($bytes), [System.Net.WebSockets.WebSocketMessageType]::Text, $true, $ct).GetAwaiter().GetResult() | Out-Null
  do {
    $stream = [IO.MemoryStream]::new()
    do {
      $buffer = [byte[]]::new(65536)
      $result = $ws.ReceiveAsync([ArraySegment[byte]]::new($buffer), $ct).GetAwaiter().GetResult()
      $stream.Write($buffer, 0, $result.Count)
    } until ($result.EndOfMessage)
    $message = [Text.Encoding]::UTF8.GetString($stream.ToArray()) | ConvertFrom-Json
    $stream.Dispose()
  } until ($message.id -eq $id)
  if ($message.error) { throw ($message.error | ConvertTo-Json) }
  return $message.result
}
try {
  Cdp 'Page.enable' @{} | Out-Null
  foreach ($width in @(1440, 390, 320)) {
    Cdp 'Emulation.setDeviceMetricsOverride' @{width=$width;height=900;deviceScaleFactor=1;mobile=$false} | Out-Null
    Cdp 'Page.navigate' @{url='http://127.0.0.1:8091/index.html'} | Out-Null
    $expression = @'
(async () => {
  const check = (condition, message) => { if (!condition) throw Error(message); };
  for (let i = 0; i < 100 && !document.querySelector('.aira-launch'); i++) await new Promise(r => setTimeout(r, 50));
  const host = document.getElementById('aira-chat');
  const query = s => host.querySelector(s);
  const calls = [];
  window.fetch = async (url, options) => { calls.push({url, payload: JSON.parse(options.body)}); return {ok:true,json:async()=>({success:'true'})}; };
  check(host && !host.hidden, 'Widget missing');
  check(window.scrollY === 0, 'Widget moved the page on startup');
  query('.aira-launch').click();
  check(!query('.aira-panel').hidden && document.activeElement.id === 'aira-question', 'Open/focus failed');
  const rect = query('.aira-panel').getBoundingClientRect();
  check(rect.left >= 0 && rect.right <= innerWidth && rect.top >= 0, 'Panel outside viewport');
  const form = query('.aira-question');
  const ask = text => { form.elements.question.value = text; form.requestSubmit(); };
  ask('Can you host on-premise?');
  check(query('.aira-messages').lastElementChild.textContent.includes('air-gapped'), 'Deployment matching failed');
  ask('What is the weather?');
  check(query('.aira-messages').lastElementChild.textContent.includes('prepared answer'), 'Unknown fallback failed');
  ask('<img src=x onerror=alert(1)>');
  check(!query('.aira-messages').querySelector('img'), 'User text interpreted as HTML');
  check(calls.length === 0, 'FAQ used network');
  query('.aira-contact').click();
  const lead = query('.aira-lead');
  const fill = () => { lead.elements.name.value='Test User';lead.elements.email.value='test@example.com';lead.elements.message.value='Demo request'; };
  fill();
  window.AIRA_CONFIG.recipient = '';
  lead.requestSubmit(); await new Promise(r=>setTimeout(r,20));
  check(calls.length === 0 && query('.aira-status').textContent.includes('not available'), 'Empty recipient not blocked');
  window.AIRA_CONFIG.recipient='team@example.com';
  lead.requestSubmit();
  await new Promise(r=>setTimeout(r, 20));
  check(calls.length === 1 && !('conversation' in calls[0].payload), 'Unconsented transcript included');
  check(calls[0].url.endsWith('team%40example.com'), 'Wrong recipient');
  check(query('.aira-status').textContent.includes('accepted'), 'Success missing');
  fill(); lead.elements.includeTranscript.checked=true;
  lead.requestSubmit(); await new Promise(r=>setTimeout(r,20));
  check(calls[1].payload.conversation.includes('on-premise'), 'Opt-in transcript missing');
  fill();
  window.fetch = async () => ({ok:true,json:async()=>({success:'false'})});
  lead.requestSubmit(); await new Promise(r=>setTimeout(r,20));
  check(query('.aira-status').textContent.includes('couldn’t confirm') && lead.elements.name.value === 'Test User', 'Provider rejection discarded form');
  window.fetch = async () => { throw Error('offline'); };
  lead.requestSubmit(); await new Promise(r=>setTimeout(r,20));
  check(!query('.aira-send').disabled && lead.elements.message.value === 'Demo request', 'Network failure recovery failed');
  let resolve;
  let pendingCalls=0;
  window.fetch = () => { pendingCalls++; return new Promise(r => {resolve=r;}); };
  lead.requestSubmit();lead.requestSubmit();
  check(pendingCalls===1, 'Duplicate submission allowed');
  resolve({ok:true,json:async()=>({success:true})});await new Promise(r=>setTimeout(r,20));
  for(let i=0;i<35;i++) ask('about');
  check(query('.aira-messages').children.length===60, 'Transcript not bounded');
  host.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
  check(query('.aira-panel').hidden && document.activeElement===query('.aira-launch'), 'Escape/focus return failed');
  await query('.aira-avatar').decode();
  check(query('.aira-avatar').naturalWidth>0, 'Avatar missing');
  return 'PASS: '+innerWidth+'px; FAQ, fallback, safe text, consent, recipient, mocked delivery, failures, duplicate prevention, keyboard, avatar';
})()
'@
    $result = Cdp 'Runtime.evaluate' @{expression=$expression;awaitPromise=$true;returnByValue=$true}
    if ($result.exceptionDetails) { throw ($result.exceptionDetails | ConvertTo-Json -Depth 15) }
    Write-Output $result.result.value
  }
} finally { $ws.Dispose() }
