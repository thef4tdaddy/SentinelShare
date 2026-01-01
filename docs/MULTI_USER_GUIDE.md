# Multi-User / Team Support Guide

## Overview

SentinelShare now supports multiple users and teams! This allows family members, roommates, or team members to have separate accounts with their own email monitoring, rules, and forwarding settings within a single SentinelShare instance.

## Key Features

### User Management
- **Individual Accounts**: Each user has their own username, password, and profile
- **User Isolation**: Users only see their own emails, rules, preferences, and email accounts
- **Admin Roles**: Admin users can manage other users (coming soon)

### User-Specific Settings
- **Forwarding Target**: Each user can set their own forwarding email address (replaces global `WIFE_EMAIL`)
- **Email Accounts**: Users can connect their own IMAP accounts
- **Rules & Preferences**: Users manage their own blocking rules and forwarding preferences
- **Categories**: Users can create custom category rules for their receipts

## Migration from Single-User Mode

### Automatic Migration

If you're upgrading from a single-user deployment:

1. **Existing Data Preserved**: All your existing email records, rules, and preferences will be preserved
2. **Legacy Admin User**: On first run, if `DASHBOARD_PASSWORD` is set and no users exist:
   - A default admin user will be created automatically
   - Username: `admin`
   - Password: Your `DASHBOARD_PASSWORD`
   - Email: Your `WIFE_EMAIL` or `admin@localhost`
3. **User Assignment**: After the admin user is created, you should manually assign `user_id` to existing records (see below)

### Manual Data Migration

To properly associate existing data with the admin user:

```bash
# Connect to your database
sqlite3 local_dev.db  # or your production database

# Find the admin user's ID
SELECT id, username FROM user WHERE username = 'admin';
# Note the ID (should be 1 for first user)

# Update existing records to assign them to the admin user
UPDATE processedemail SET user_id = 1 WHERE user_id IS NULL;
UPDATE emailaccount SET user_id = 1 WHERE user_id IS NULL;
UPDATE preference SET user_id = 1 WHERE user_id IS NULL;
UPDATE manualrule SET user_id = 1 WHERE user_id IS NULL;
UPDATE categoryrule SET user_id = 1 WHERE user_id IS NULL;
UPDATE learningcandidate SET user_id = 1 WHERE user_id IS NULL;
UPDATE stats SET user_id = 1 WHERE user_id IS NULL;
```

## Setup Guide

### For New Deployments

1. **Set Environment Variables**:
   ```bash
   SECRET_KEY=your-secret-key-here
   ALLOW_REGISTRATION=true  # Allow new users to register
   ```

2. **Start the Application**:
   ```bash
   docker-compose up -d
   ```

3. **Register the First User**:
   - Navigate to the registration page
   - Create an admin account
   - The first user is typically made an admin

4. **Configure User Settings**:
   - Set your forwarding target email
   - Add your email accounts
   - Configure your rules and preferences

### For Existing Deployments

1. **Backup Your Database**:
   ```bash
   cp local_dev.db local_dev.db.backup
   ```

2. **Update Code**:
   ```bash
   git pull origin main
   pip install -r requirements.txt
   ```

3. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start Application**:
   - The first time you start, if `DASHBOARD_PASSWORD` is set, a legacy admin user will be created
   - Login with username `admin` and your `DASHBOARD_PASSWORD`

5. **Migrate Data** (if needed):
   - Follow the manual data migration steps above

6. **Add Additional Users**:
   - Either enable registration (`ALLOW_REGISTRATION=true`)
   - Or have the admin create users via the admin panel (coming soon)

## Environment Variables

### New Variables

- `ALLOW_REGISTRATION`: Set to `true` to allow new user registrations (default: `true`)
- `FRONTEND_URL`: Base URL for frontend redirects (optional)

### Changed Variables

- `DASHBOARD_PASSWORD`: Still supported for backward compatibility
  - In multi-user mode, creates/authenticates legacy admin user
  - Can be removed once you've migrated to user-based auth

### Per-User Variables (No longer global)

These settings are now per-user, configurable in the web UI:
- Forwarding target email (was `WIFE_EMAIL`)
- Email accounts (was `EMAIL_ACCOUNTS`, `GMAIL_EMAIL`, etc.)

## API Changes

### Authentication Endpoints

#### POST `/api/auth/register`
Register a new user:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "secure-password",
  "forwarding_target_email": "family@example.com"
}
```

#### POST `/api/auth/login`
Login with username and password:
```json
{
  "username": "johndoe",
  "password": "secure-password"
}
```

Or legacy mode (for backward compatibility):
```json
{
  "password": "dashboard-password"
}
```

#### GET `/api/auth/me`
Returns current user info:
```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "is_admin": false,
    "forwarding_target_email": "family@example.com"
  }
}
```

### Data Access

All data endpoints now automatically filter by the authenticated user:
- `/api/dashboard/activity` - Only shows current user's emails
- `/api/settings/preferences` - Only shows current user's preferences
- `/api/settings/rules` - Only shows current user's rules
- `/api/settings/accounts` - Only shows current user's email accounts
- `/api/history/emails` - Only shows current user's email history

## Security Considerations

1. **Password Storage**: User passwords are hashed using bcrypt
2. **Data Isolation**: Users can only access their own data
3. **OAuth2 Tokens**: Stored encrypted, associated with user accounts
4. **Session Management**: Each user has their own session

## Backward Compatibility

The system maintains backward compatibility with single-user deployments:

- If no users exist and `DASHBOARD_PASSWORD` is set, a legacy admin user is auto-created
- Old session-based auth still works for backward compatibility
- Environment-based email accounts (`EMAIL_ACCOUNTS`) are still supported but should be migrated to database accounts

## Troubleshooting

### "Not authenticated" errors after upgrade

**Solution**: 
1. Clear your browser cookies/session
2. Login again with username `admin` and your `DASHBOARD_PASSWORD`

### Can't see my old emails/rules

**Solution**: Run the manual data migration SQL queries to assign `user_id` to existing records.

### "Username already exists" when trying to register

**Solution**: The legacy admin user was already created. Use username `admin` with your `DASHBOARD_PASSWORD`.

### OAuth2 email accounts not showing up

**Solution**: Re-authenticate the OAuth2 accounts so they get associated with your user account.

## Future Enhancements

Coming soon:
- Admin panel for user management
- User invitation system
- Team/organization support
- Shared rules and preferences for teams
- Audit logs for admin actions

## Support

For issues or questions:
- GitHub Issues: https://github.com/thef4tdaddy/SentinelShare/issues
- Discussions: https://github.com/thef4tdaddy/SentinelShare/discussions
