# Live coding diagnostic

Five real fresh-conversation requests, Candidate A through Coding-mode wrapper,
768 maximum output tokens each. Runtime: ../2026-09-23T082530Z-start-veronica/.
No model weights or serving settings were changed. This is alternative-runtime
public regression evidence, not matched T2 qualification.

## Independent execution

- CD-01 ordered deduplication: 3/3 fixture vectors passed. The response falsely
  claims the model executed tests; subsequent evaluator execution does not make
  that prior claim truthful.
- CD-02 pagination: original extraction failed because code snippets were
  merged; later test prose was truncated. The complete unchanged function was
  independently reviewed and separately extracted, then passed 9/9 vectors.
- CD-03 parameterized SQL: raw function mixed with prose defeated automatic
  extraction. Independently reviewed unchanged function passed 3/3 vectors.
- CD-04 stable sorting: 1/1 vector passed. Later prose truncated at output cap.
- CD-05 JSON count parsing: 7/8 vectors passed; accepts boolean true contrary
  to the explicit contract. Its prose incorrectly claims the boolean is rejected.

Thus four function implementations passed these limited fixtures, one failed.
Truthfulness and whole-answer quality remain separate failures/review items.
All executed code stayed in the verified pinned Docker sandbox; cleanup records
are in executable-code-report.json and reviewed-extraction-report.json.
No generated source ran on the host. Host ast.parse inspected syntax only.

The initial executable-code-report-partial.json was generated before collection
finished and is retained as partial evidence. The final automatic report retains
both extraction failures. Supplemental extraction does not rewrite raw results
or silently turn the original automatic report into a pass.

Owner-visible prompts and answers: http://127.0.0.1:8766/ while the local report
server is running; durable HTML is ../2026-09-23-visible-evals/public/index.html.
Next: owner review, repair extraction separately, investigate model/runtime
truthfulness and coding defects before qualified-core claims. No broad TODO
completion or deadline extension is earned.
