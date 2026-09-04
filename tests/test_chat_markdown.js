const assert = require("assert");
const {
  escapeHtml,
  markdownToSafeHtml,
  serializeConversation,
  deserializeConversation,
} = require("../src/veronica_core/static/app.js");

assert.equal(escapeHtml('<img src=x onerror=alert(1)>'), "&lt;img src=x onerror=alert(1)&gt;");

const html = markdownToSafeHtml([
  "Hello <script>alert(1)</script>",
  "**bold** and `code`",
  "```js\nalert(1)\n```",
  "[ok](https://example.com) [bad](javascript:alert(1))",
  "- one\n- two",
].join("\n\n"));

assert.ok(!html.includes("<script>"));
assert.ok(html.includes("&lt;script&gt;"));
assert.ok(html.includes("<strong>bold</strong>"));
assert.ok(html.includes("<code>code</code>"));
assert.ok(html.includes("<pre><code class=\"language-js\">alert(1)</code></pre>"));
assert.ok(html.includes('href="https://example.com"'));
assert.ok(!/href=["']javascript:/i.test(html));
assert.ok(html.includes("[bad](javascript:alert(1))") || html.includes("javascript:alert(1)"));
assert.ok(html.includes("<ul><li>one</li><li>two</li></ul>"));

const restored = deserializeConversation(serializeConversation(
  [{ role: "user", content: "Hi" }, { role: "assistant", content: "Hello", status: "streaming" }],
  "coding",
));
assert.equal(restored.mode, "coding");
assert.equal(restored.messages[1].status, "stopped");
assert.equal(deserializeConversation("not-json"), null);
assert.deepEqual(deserializeConversation(JSON.stringify({ messages: [{ role: "tool", content: "nope" }] })).messages, []);

console.log("ok");
