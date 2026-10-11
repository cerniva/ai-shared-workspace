# Archive integrity check — 2026-10-12

Base commit: b0f50118868425ebcce660e0898659b97583d558.
Archive blob: cec1c80e04d9c9d86ac08f5e79c38e4450184df7.
Found three suspect standalone lines: 5026, 5092, 5139.
Verified 312 message IDs would survive exact-line removal; 308 older IDs preserved. Historical comparison retained 4348 substantive lines in order.
No protected archive was changed. Code and archive writes were denied by connector security. No new CI was run. Status: BLOCKED_WRITE.
Next: authorized agent to apply a SHA-guarded lossless fix in a draft PR, test and read back. No workflow, secret, OAuth, publishing or merge actions.
