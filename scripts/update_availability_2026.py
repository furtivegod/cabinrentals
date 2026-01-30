#!/usr/bin/env python3
"""
Standalone script to update availability_calendar_availability table for year 2026
based on Streamline API data.

This script:
1. Fetches all cabins with Streamline IDs and calendar IDs
2. Gets availability data from Streamline API for 2026
3. Calculates calendar states (check-in, check-out, booked, turn-around)
4. Updates the availability_calendar_availability table

Usage:
    python update_availability_2026.py

Requirements:
    - SUPABASE_URL and SUPABASE_KEY in .env file
    - STREAMLINE_API_URL, STREAMLINE_TOKEN_KEY, STREAMLINE_TOKEN_SECRET in .env file
    - pip install supabase httpx python-dotenv
"""

import sys
import os
import asyncio
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from supabase import create_client, Client
import httpx

# Load environment variables
load_dotenv()

# Calendar state IDs (matching Drupal)
STATE_IDS = {
    'cal-available': 5,
    'cal-in': 6,
    'cal-out': 7,
    'cal-inout': 8,
    'cal-booked': 9,
}


class AvailabilityUpdater:
    """Updates availability calendar data from Streamline API"""
    
    def __init__(self):
        """Initialize connections to Supabase and Streamline"""
        # Supabase connection
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY are required. "
                "Please set them in your .env file."
            )
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Streamline API credentials
        self.streamline_url = os.getenv('STREAMLINE_API_URL', 'https://web.streamlinevrs.com/api/json')
        self.streamline_token_key = os.getenv('STREAMLINE_TOKEN_KEY')
        self.streamline_token_secret = os.getenv('STREAMLINE_TOKEN_SECRET')
        
        if not self.streamline_token_key or not self.streamline_token_secret:
            raise ValueError(
                "STREAMLINE_TOKEN_KEY and STREAMLINE_TOKEN_SECRET are required. "
                "Please set them in your .env file."
            )
        
        # Date range for 2026
        self.start_date = date(2026, 1, 1)
        self.end_date = date(2026, 12, 31)
        
        print("=" * 70)
        print("Availability Calendar Updater for 2026")
        print("=" * 70)
        print(f"Date Range: {self.start_date} to {self.end_date}")
        print(f"Streamline API: {self.streamline_url}")
        print()
    
    async def fetch_streamline_availability(
        self, 
        streamline_id: int
    ) -> Optional[Dict]:
        """
        Fetch availability data from Streamline API for a property
        
        Args:
            streamline_id: Streamline property/unit ID
            
        Returns:
            API response data or None if error
        """
        payload = {
            "methodName": "GetPropertyAvailabilityCalendarRawData",
            "params": {
                "token_key": self.streamline_token_key,
                "token_secret": self.streamline_token_secret,
                "unit_id": streamline_id,
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.streamline_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check for API errors
                if isinstance(data, dict):
                    if "status" in data:
                        status = data.get("status", {})
                        if isinstance(status, dict):
                            code = status.get("code")
                            if code is not None and code != 0:
                                error_msg = status.get("description", "Unknown error")
                                
                                # Handle specific error cases
                                if "not found" in error_msg.lower() or "property/unit id was not found" in error_msg.lower():
                                    print(f"  ℹ Property not found in Streamline (may be inactive or removed)")
                                    return None
                                else:
                                    print(f"  ⚠ Streamline API Error: {error_msg}")
                                    return None
                
                return data
                
        except httpx.HTTPStatusError as e:
            print(f"  ⚠ HTTP Error {e.response.status_code}: {e.response.text[:100]}")
            return None
        except httpx.RequestError as e:
            print(f"  ⚠ Request Error: {str(e)}")
            return None
        except Exception as e:
            print(f"  ⚠ Unexpected Error: {str(e)}")
            return None
    
    def calculate_states(
        self, 
        blocked_periods: List[Dict], 
        calendar_id: int
    ) -> Dict[str, int]:
        """
        Calculate calendar states from blocked periods
        
        Implements the same logic as Drupal's crog_calendar_batch_streamline_update_availability_v2()
        
        Args:
            blocked_periods: List of blocked period dicts with startdate/enddate
            calendar_id: Calendar ID for this cabin
            
        Returns:
            Dictionary mapping date strings (YYYY-MM-DD) to state IDs
        """
        states = {}
        
        # Sort periods by start date to process in order
        sorted_periods = sorted(
            blocked_periods,
            key=lambda p: p.get('startdate', '')
        )
        
        for period_idx, period in enumerate(sorted_periods):
            startdate_str = period.get('startdate')
            enddate_str = period.get('enddate')
            
            if not startdate_str or not enddate_str:
                continue
            
            try:
                # Parse dates - Streamline returns dates in MM/DD/YYYY format
                # Try MM/DD/YYYY first (Streamline format), then YYYY-MM-DD
                def parse_date(date_str: str) -> Optional[date]:
                    """Parse date string in multiple formats"""
                    formats = ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y']
                    for fmt in formats:
                        try:
                            return datetime.strptime(date_str, fmt).date()
                        except ValueError:
                            continue
                    return None
                
                start = parse_date(startdate_str)
                end = parse_date(enddate_str)
                
                if start is None or end is None:
                    print(f"  ⚠ Invalid date format: start={startdate_str}, end={enddate_str}")
                    continue
                
                # IMPORTANT: enddate is the last reserved day, check-out is the day after
                # Example: start=02/07, end=02/08 means:
                #   - 02/07 = check-in
                #   - 02/08 = reserved (last day of stay)
                #   - 02/09 = check-out (day after enddate)
                checkout_date = end + timedelta(days=1)
                
                # Only process dates in 2026
                if start > self.end_date:
                    continue
                
                # Clamp dates to 2026 range
                # Include checkout_date if it's within 2026
                period_start = max(start, self.start_date)
                # Set period_end to include checkout_date (if within 2026)
                if checkout_date <= self.end_date:
                    period_end = checkout_date + timedelta(days=1)  # +1 to include checkout_date in loop
                else:
                    period_end = self.end_date + timedelta(days=1)  # Stop at end of 2026
                
                # Process each day in the period
                current_date = period_start
                
                while current_date < period_end:
                    # Only process dates within 2026
                    if current_date > self.end_date:
                        break
                    
                    date_str = current_date.strftime('%Y-%m-%d')
                    
                    # Determine state based on position in period
                    if current_date == start:
                        # First day: check-in logic (matching Drupal lines 802-823)
                        existing_sid = states.get(date_str)
                        
                        if existing_sid is None:
                            # No existing state: set as check-in
                            states[date_str] = STATE_IDS['cal-in']
                        elif existing_sid == STATE_IDS['cal-in']:
                            # Already check-in: keep it
                            states[date_str] = STATE_IDS['cal-in']
                        elif existing_sid == STATE_IDS['cal-out']:
                            # Turn-around: check-out + check-in on same day
                            states[date_str] = STATE_IDS['cal-inout']
                        elif existing_sid == STATE_IDS['cal-inout']:
                            # Already turn-around: keep it
                            states[date_str] = STATE_IDS['cal-inout']
                        else:
                            # Other state (booked): change to check-in
                            states[date_str] = STATE_IDS['cal-in']
                    
                    elif current_date == checkout_date:
                        # Day after enddate: check-out
                        states[date_str] = STATE_IDS['cal-out']
                    
                    elif start < current_date <= end:
                        # Days from start+1 to enddate (inclusive): booked/reserved
                        states[date_str] = STATE_IDS['cal-booked']
                    
                    current_date += timedelta(days=1)
                
            except ValueError as e:
                print(f"  ⚠ Invalid date format in period: {e}")
                continue
        
        return states
    
    def get_cabins_with_calendars(self) -> List[Dict]:
        """Get all cabins with calendar mappings"""
        try:
            result = self.supabase.from_('cabin_calendar_mapping').select(
                'calendar_id, streamline_id, cabin_id'
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"✗ Error fetching cabins: {e}")
            return []
    
    async def update_cabin_availability(
        self, 
        calendar_id: int, 
        streamline_id: int,
        cabin_id: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Update availability for a single cabin
        
        Returns:
            Tuple of (inserted_count, updated_count)
        """
        print(f"\nProcessing Calendar ID {calendar_id} (Streamline ID: {streamline_id})...")
        
        # Fetch availability from Streamline
        print(f"  Fetching availability from Streamline API...")
        availability_data = await self.fetch_streamline_availability(streamline_id)
        
        if not availability_data:
            print(f"  ⚠ No availability data returned")
            return (0, 0)
        
        # Extract blocked periods
        blocked_periods = []
        
        if isinstance(availability_data, dict):
            data = availability_data.get('data', {})
            
            # Handle single blocked_period object
            if 'blocked_period' in data:
                bp = data['blocked_period']
                if isinstance(bp, dict) and 'startdate' in bp:
                    blocked_periods.append(bp)
                elif isinstance(bp, list):
                    blocked_periods.extend(bp)
        
        if not blocked_periods:
            print(f"  ℹ No blocked periods found (cabin is fully available)")
            # Delete existing 2026 records to mark as available
            self._delete_2026_availability(calendar_id)
            return (0, 0)
        
        print(f"  Found {len(blocked_periods)} blocked period(s)")
        
        # Calculate states
        states = self.calculate_states(blocked_periods, calendar_id)
        
        if not states:
            print(f"  ℹ No dates in 2026 range")
            return (0, 0)
        
        print(f"  Calculated {len(states)} date states")
        
        # Update database
        inserted, updated = self._update_database(calendar_id, states)
        
        print(f"  ✓ Updated: {updated} records, Inserted: {inserted} records")
        
        return (inserted, updated)
    
    def _delete_2026_availability(self, calendar_id: int):
        """Delete existing 2026 availability records"""
        try:
            self.supabase.from_('availability_calendar_availability').delete().eq(
                'cid', calendar_id
            ).gte('date', str(self.start_date)).lte('date', str(self.end_date)).execute()
        except Exception as e:
            print(f"  ⚠ Error deleting old records: {e}")
    
    def _update_database(
        self, 
        calendar_id: int, 
        states: Dict[str, int]
    ) -> Tuple[int, int]:
        """
        Update availability_calendar_availability table
        
        Uses upsert logic to handle duplicates gracefully.
        
        Returns:
            Tuple of (inserted_count, updated_count)
        """
        inserted = 0
        updated = 0
        
        # Get existing records for this calendar in 2026 (with timeout handling)
        existing = {}
        try:
            # Fetch in smaller batches to avoid timeout
            date_list = list(states.keys())
            batch_size = 100
            
            for i in range(0, len(date_list), batch_size):
                batch = date_list[i:i + batch_size]
                try:
                    existing_result = self.supabase.from_('availability_calendar_availability').select(
                        'date, sid'
                    ).eq('cid', calendar_id).in_('date', batch).execute()
                    
                    for record in (existing_result.data or []):
                        existing[record['date']] = record['sid']
                except Exception as e:
                    # If batch fails, continue with next batch
                    print(f"  ⚠ Warning: Error fetching batch {i//batch_size + 1}: {e}")
                    continue
        except Exception as e:
            print(f"  ⚠ Warning: Error fetching existing records: {e}")
            print(f"  Will use upsert logic to handle duplicates")
        
        # Process each date with upsert logic
        for date_str, sid in states.items():
            try:
                if date_str in existing:
                    # Update existing record if state changed
                    if existing[date_str] != sid:
                        self.supabase.from_('availability_calendar_availability').update(
                            {'sid': sid}
                        ).eq('cid', calendar_id).eq('date', date_str).execute()
                        updated += 1
                else:
                    # Try to insert, but handle duplicate key errors gracefully
                    try:
                        self.supabase.from_('availability_calendar_availability').insert({
                            'cid': calendar_id,
                            'date': date_str,
                            'sid': sid
                        }).execute()
                        inserted += 1
                    except Exception as insert_error:
                        # If insert fails due to duplicate, try update instead
                        error_str = str(insert_error)
                        if 'duplicate key' in error_str.lower() or '23505' in error_str:
                            # Record exists but wasn't in our existing dict (race condition or timeout)
                            # Update it instead
                            try:
                                self.supabase.from_('availability_calendar_availability').update(
                                    {'sid': sid}
                                ).eq('cid', calendar_id).eq('date', date_str).execute()
                                updated += 1
                            except Exception as update_error:
                                print(f"  ⚠ Error updating date {date_str}: {update_error}")
                        else:
                            print(f"  ⚠ Error inserting date {date_str}: {insert_error}")
            except Exception as e:
                print(f"  ⚠ Error updating date {date_str}: {e}")
                continue
        
        return (inserted, updated)
    
    async def run(self):
        """Main execution method"""
        # Get all cabins with calendars
        print("Fetching cabins with calendar mappings...")
        cabins = self.get_cabins_with_calendars()
        
        if not cabins:
            print("✗ No cabins found with calendar mappings")
            return
        
        print(f"✓ Found {len(cabins)} cabin(s) to process\n")
        
        total_inserted = 0
        total_updated = 0
        successful = 0
        skipped = 0  # Properties not found or no data
        failed = 0   # Actual errors
        
        # Process each cabin
        for i, cabin in enumerate(cabins, 1):
            calendar_id = cabin.get('calendar_id')
            streamline_id = cabin.get('streamline_id')
            cabin_id = cabin.get('cabin_id')
            
            if not calendar_id or not streamline_id:
                print(f"\n[{i}/{len(cabins)}] Skipping: Missing calendar_id or streamline_id")
                skipped += 1
                continue
            
            print(f"\n[{i}/{len(cabins)}] ", end="")
            
            try:
                inserted, updated = await self.update_cabin_availability(
                    calendar_id, 
                    streamline_id,
                    cabin_id
                )
                
                # Check if this was a "not found" case (no data returned)
                if inserted == 0 and updated == 0:
                    # Check if we got an error (property not found)
                    # This is handled in fetch_streamline_availability
                    skipped += 1
                else:
                    total_inserted += inserted
                    total_updated += updated
                    successful += 1
            except Exception as e:
                print(f"  ✗ Error: {e}")
                failed += 1
                continue
        
        # Summary
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        print(f"Total Cabins Processed: {len(cabins)}")
        print(f"  ✓ Successful: {successful}")
        print(f"  ⊘ Skipped (not found/no data): {skipped}")
        print(f"  ✗ Failed (errors): {failed}")
        print(f"\nDatabase Updates:")
        print(f"  • Inserted: {total_inserted} records")
        print(f"  • Updated: {total_updated} records")
        print(f"  • Total: {total_inserted + total_updated} records")
        print("=" * 70)
        
        if skipped > 0:
            print("\nNote: Some properties were skipped because:")
            print("  - Property not found in Streamline (may be inactive or removed)")
            print("  - No availability data returned")
            print("  - Missing calendar_id or streamline_id")


async def main():
    """Main entry point"""
    try:
        updater = AvailabilityUpdater()
        await updater.run()
    except ValueError as e:
        print(f"\n✗ Configuration Error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_KEY")
        print("  - STREAMLINE_API_URL (optional, defaults to https://web.streamlinevrs.com/api/json)")
        print("  - STREAMLINE_TOKEN_KEY")
        print("  - STREAMLINE_TOKEN_SECRET")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

