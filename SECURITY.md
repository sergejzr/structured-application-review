# Security and privacy

Application documents contain personal data. Do not commit candidate documents,
generated profiles, API keys, or access tokens. The repository ignores common
input/output directories, but users must still verify `git status` before pushing.

Before processing real applications, confirm that the configured LLM endpoint is
approved for the data and document the applicable retention policy. Use a local
or institutionally approved endpoint where possible. Treat generated evidence,
summaries, and inconsistency notes as sensitive data.

If a credential is ever committed, revoke it immediately and remove it from the
credential store; deleting it in a later commit is not sufficient.
