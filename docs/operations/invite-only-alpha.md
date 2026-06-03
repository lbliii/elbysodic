# Invite-Only Alpha Runbook

This runbook is the narrow operating path for Elbysodic's first real realm:
one director-owned realm, invite-only access, SQLite on a single Railway
replica, and explicit smoke evidence before writers are invited.

## 1. Prepare

- Read `docs/operations/production-bootstrap.md`.
- Confirm the Railway Volume and database path through Studio Operations.
- Take a SQLite backup or confirm the database is empty.
- Keep `public-preview` off until signed-out privacy smoke passes.

## 2. Bootstrap

- Run `elbysodic bootstrap-first-realm` only after the go criteria pass.
- Log in as the director.
- Verify `/studio/operations` shows the expected environment, database path,
  schema version, migration ledger, realm count, and launch status.
- Confirm `/studio/launch` starts at `backstage`.

## 3. Shape The Realm

- Use Realm Builder for the minimum opening packet.
- Add or review premise, application guide, scene hub, claims posture, wanted
  hooks, and appearance.
- Keep the launch checklist green before inviting writers.

## 4. Open Invite-Only

- Set launch status to `invite-only`.
- Create one writer invitation.
- Copy the link immediately; alpha delivery is copy-only.
- If the link is lost or shared with the wrong person while it is still
  pending, use `Reissue invitation` to revoke it and create a fresh invitation
  for the same email.
- Confirm expired, revoked, and accepted links do not grant access.
- When inviting an existing Elbysodic account into another realm, acceptance
  reuses the global account but creates membership and any first face only in
  the invited realm.
- If a prospect submitted request-access before logging in, a later signed-in
  duplicate for the same email should link that account to the existing open
  request instead of creating a second queue item or granting membership.

### Invitation Delivery Policy

Until an email sender is configured and approved, Elbysodic does not claim that
Studio can send, resend, or recover an invitation link. Directors see the raw
invite URL only in the creation response because the database stores only a
token hash. The supported recovery path is reissue: revoke the still-pending
invitation, create a new invitation for the same email, copy the new URL, and
keep the old invitation row plus any linked access-request activity as audit
history.

Accepted, revoked, and expired invitations are terminal for link delivery. Do
not reissue them as though the same token can be recovered. If a writer already
accepted the invitation, use membership support workflows instead of creating a
second invite.

## 5. Smoke

- Run the Railway smoke checklist.
- Confirm restart persistence for launch status, realm content, director login,
  writer membership, and invitation state.
- Confirm public `/network` does not expose the realm until launch status is
  `public-preview` and public-ready content exists.

## 6. Decide

Stay invite-only unless all are true:

- backup/restore has been rehearsed recently
- notification/sidebar privacy tests are green
- public catalog copy is intentional
- signed-out preview routes expose only published public content
- directors understand invite revoke and copy-only delivery

Record the alpha decision with date, URL, launch status, smoke result, backup
path, and any deferred risks.
