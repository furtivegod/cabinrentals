# Availability Calendar Update Scripts

## update_availability_2026.py

Standalone script to update the `availability_calendar_availability` table for year 2026 based on Streamline API data.

### Features

- Fetches all cabins with Streamline IDs and calendar IDs from Supabase
- Retrieves availability data from Streamline API for 2026
- Calculates calendar states:
  - **Check-in** (`cal-in`, sid=6): First day of reservation
  - **Check-out** (`cal-out`, sid=7): Last day of reservation
  - **Booked** (`cal-booked`, sid=9): Middle days of reservation
  - **Turn-around** (`cal-inout`, sid=8): Same day check-out/check-in
- Updates Supabase database with calculated states
- Handles errors gracefully and provides detailed progress output

### Requirements

```bash
pip install supabase httpx python-dotenv
```

### Environment Variables

Create a `.env` file in the `backend` directory with:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key

# Streamline API
STREAMLINE_API_URL=https://web.streamlinevrs.com/api/json
STREAMLINE_TOKEN_KEY=your-token-key
STREAMLINE_TOKEN_SECRET=your-token-secret
```

### Usage

```bash
# From the backend directory
python scripts/update_availability_2026.py

# Or from project root
cd backend
python scripts/update_availability_2026.py
```

### How It Works

1. **Fetches Cabin Mappings**: Gets all cabins from `cabin_calendar_mapping` table
2. **Streamline API Call**: For each cabin, calls `GetPropertyAvailabilityCalendarRawData`
3. **State Calculation**: 
   - Processes blocked periods from Streamline
   - Calculates check-in, check-out, booked, and turn-around states
   - Handles overlapping reservations (turn-around days)
4. **Database Update**: 
   - Updates existing records if state changed
   - Inserts new records for new dates
   - Only processes dates in 2026

### State Calculation Logic

Based on the Drupal implementation:

- **First day of reservation** → `cal-in` (check-in)
- **Last day of reservation** → `cal-out` (check-out)
- **Middle days** → `cal-booked` (fully reserved)
- **Turn-around day**: When check-out date equals next check-in date → `cal-inout`

### Example Output

```
======================================================================
Availability Calendar Updater for 2026
======================================================================
Date Range: 2026-01-01 to 2026-12-31
Streamline API: https://web.streamlinevrs.com/api/json

Fetching cabins with calendar mappings...
✓ Found 25 cabin(s) to process

[1/25] Processing Calendar ID 65 (Streamline ID: 70207)...
  Fetching availability from Streamline API...
  Found 12 blocked period(s)
  Calculated 45 date states
  ✓ Updated: 30 records, Inserted: 15 records

...

======================================================================
Summary
======================================================================
Total Cabins Processed: 25
  ✓ Successful: 24
  ✗ Failed: 1

Database Updates:
  • Inserted: 180 records
  • Updated: 320 records
  • Total: 500 records
======================================================================
```

### Notes

- The script only updates data for **year 2026**
- Dates without blocked periods are treated as available (no database record needed)
- Existing records are updated if the state changes
- The script is idempotent - safe to run multiple times

### Troubleshooting

**Error: SUPABASE_URL and SUPABASE_KEY are required**
- Check your `.env` file has the correct Supabase credentials

**Error: STREAMLINE_TOKEN_KEY and STREAMLINE_TOKEN_SECRET are required**
- Ensure Streamline API credentials are set in `.env`

**HTTP Error 403 or IP whitelisting error**
- Streamline API may require IP whitelisting
- Contact Streamline support to whitelist your IP address

**No availability data returned**
- Check if the Streamline ID is correct
- Verify API credentials are valid
- Check if property has any reservations in 2026

