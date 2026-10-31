# Security and QA checklist

## Implemented safeguards

- CSRF protection is enabled globally through Flask-WTF. Every POST form includes a CSRF token.
- Production mode requires `APP_ENV=production` and a non-empty `SECRET_KEY`.
- Production session and remember cookies are `Secure`, `HttpOnly`, and `SameSite=Lax`.
- Flask-Login uses strong session protection.
- Application detail/edit/delete/archive/event/interview/status routes scope records to the signed-in user.
- Task update/delete routes scope records to the signed-in user; task creation verifies ownership of a linked application.
- Server-side validation covers required values, field lengths, dates, dropdown choices, email addresses, URLs, task priority, and linked application ownership.
- Account deletion requires the current password and an explicit browser confirmation. Password changes require the current password and sign the user out afterward.
- CSV import skips invalid rows and duplicate company + role + application-date combinations for the current account. It reports imported, invalid, and duplicate row counts.
- Existing SQLite records are preserved by the additive schema migration routine.

## Manual verification before public deployment

1. Create two test accounts (User A and User B).
2. Add an application and a task as User A. Sign in as User B and try User A's application and task URLs using their numeric IDs. The requests should return 404 and must not show or modify User A's data.
3. Submit a POST request without a CSRF token. It should be rejected with HTTP 400.
4. Try invalid dates, oversized text, an invalid recruiter email, a non-HTTP URL, invalid dropdown values, and an invalid task priority. The app should show an error and should not save the record.
5. Select `Other` for status, interview type, employment type, priority, and source. Confirm the companion field appears and is required; submit without its value and confirm the server rejects it.
6. Import a CSV containing a valid row, a duplicate row, a missing company/role, and an invalid date. Confirm only valid non-duplicate rows are saved and the skipped counts are reported.
7. Archive an application. Confirm it disappears from the active dashboard, analytics, board, calendar and top-company data; restore it and confirm it returns.
8. Add two interview rounds to one application and confirm both appear in its details.
9. Create overdue and future tasks/follow-ups and confirm dashboard alerts and task labels are correct.
10. With no active applications, open the dashboard and board. Confirm the empty states render and no chart division-by-zero error occurs.
11. Test profile update, password change (including wrong current password), and account deletion (including wrong current password). Confirm account deletion removes the user's related records.
12. For migration verification, back up the existing SQLite database first, run the updated app against a copy, and confirm old users/applications remain present after startup.
13. Test the layout at narrow mobile widths and on a desktop browser.

Do not test account deletion against a real account or run destructive tests against the only copy of your database.
