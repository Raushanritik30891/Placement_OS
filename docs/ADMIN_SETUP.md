# Admin Setup

## No public admin registration

Registration always creates a `student` account. A user cannot select or escalate their role from the public API.

For a fresh local SQLite development database:

1. Register the account through the app.
2. Stop the backend.
3. Open the SQLite database using a trusted local SQLite administration tool.
4. Run the following statement, replacing the email with the verified account address:

```sql
UPDATE users SET role = 'admin' WHERE email = 'verified-admin@example.com';
```

5. Restart the backend and sign in again so the new role is reflected in the access token.

Do not expose database credentials or an admin-promotion endpoint to the public application.

For production, promote administrators only through a controlled operator workflow and an audited database migration/administrative command. Use a unique JWT secret and secure database credentials.

## Current admin capabilities

- Create topics.
- Create problem drafts.
- Store public sample inputs and expected outputs.
- Add hidden server-side test cases.
- Publish or unpublish problems.
- Hidden test values are not included in public problem responses.

A problem cannot be published until at least one public sample and one hidden test case exist. Before publishing, review its statement, constraints, sample output, time/space complexity, hints and all test cases.

## Still required for a production admin system

- User management and audit log UI.
- Edit/delete workflows with approvals and revision history.
- Bulk import/export and dataset upload.
- Test-case quality review and execution diagnostics.
- CSRF/rate-limiting controls appropriate to deployment.
- Database backups and operator access logging.
