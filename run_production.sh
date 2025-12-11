#!/bin/bash
# run_production.sh

# 1. Set the Remote Database URL (Neon)
# This ensures that when we create "Tracking Logs", they are saved in the cloud DB,
# so the Render server can actually find them when people click.
export DATABASE_URL='postgresql://neondb_owner:npg_ZcJ5YiX1Blzn@ep-wild-mud-aeq1r92j-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require'

# 2. Set the Site URL 
# This ensures links generated in the email point to your live site, not localhost.
# REPLACE THIS with your actual Render URL if it's different!
export SITE_URL='https://send-email-app.onrender.com'

# 3. Security (Optional for local run, but good practice)
export DEBUG='False'

echo "🔌 Connecting to Production Database (Neon)..."
echo "🔗 Using Site URL: $SITE_URL"

# 4. Run the command passed to this script
# Example usage: ./run_production.sh python manage.py send_cold_emails
"$@"
