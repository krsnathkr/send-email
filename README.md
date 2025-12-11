# Cold Email Campaign Project

Welcome! This tool allows you to send personalized bulk emails using **CSV data** and **Markdown templates**. It handles merging data (like names and companies) into your emails and sending them via your configured SMTP server (e.g., Gmail).

This guide is designed for complete beginners. Follow the steps below to set up and run your first campaign.

---

## 1. Prerequisites

Before you begin, make sure you have the following installed on your computer:

*   **Python 3.x**: [Download Python](https://www.python.org/downloads/)
*   **Terminal (Mac/Linux) or Command Prompt (Windows)**: You'll use this to run commands.

---

## 2. Installation & Setup

### Step 1: Open the Project
Navigate to the project folder in your terminal.
```bash
cd /path/to/send-email
```

### Step 2: Create a Virtual Environment
A virtual environment keeps this project's dependencies separate from your system.
```bash
python3 -m venv venv
```

### Step 3: Activate the Virtual Environment
You need to "turn on" the environment every time you work on this project.
*   **Mac/Linux**:
    ```bash
    source venv/bin/activate
    ```
*   **Windows**:
    ```bash
    venv\Scripts\activate
    ```
*(You should see `(venv)` appear at the start of your terminal line).*

### Step 4: Install Dependencies
Install the required libraries (Django, Markdown, etc.).
```bash
pip install -r requirements.txt
```

### Step 5: Database Setup
Initialize the database to store campaign logs.
```bash
python manage.py migrate
```

---

## 3. Configuration

You need to tell the system your email credentials.

1.  Look for a file named `.env` in the project root. If it doesn't exist, create it.
2.  Open `.env` in a text editor and add your settings:

```env
# .env file content
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

> [!IMPORTANT]
> If you are using Gmail, you **cannot** use your normal login password. You must generate an **App Password**.
> 1. Go to your [Google Account Security](https://myaccount.google.com/security).
> 2. Enable **2-Step Verification**.
> 3. Search for "App Passwords" and create one.
> 4. Use that 16-character code as your `EMAIL_HOST_PASSWORD`.

---

## 4. Project Structure (Where things are)

*   `emails/`: The core code for the email logic.
*   `templates/`: Folder where you store your **Markdown email templates** (e.g., `web_developer.md`).
*   `test.csv`: Your **recipient list**.
*   `manage.py`: The tool used to run the send command.

---

## 5. Usage Guide

### A. Prepare Your Recipient List (CSV)
Create a CSV file (e.g., `test.csv`) with your contacts. It **must** have a header row.

**Example `test.csv`**:
```csv
email,first_name,company,role
john@example.com,John,TechCorp,Developer
jane@test.com,Jane,StartupInc,Data Scientist
```

### B. Prepare Your Email Template
Create a Markdown file (e.g., `templates/my_email.md`). Use `[column_name]` to insert data from your CSV.

**Example Template**:
```markdown
Subject: Application for [role] at [company]

Hi [first_name],

I love what [company] is doing...
```
*(Note: If you add `Subject: Your Subject Here` as the first line, it will override the command-line subject).*

### C. Run the Campaign
Use the `send_campaign` command to start sending.

**Command Structure**:
```bash
python manage.py send_campaign \
    --csv <path_to_csv> \
    --template <path_to_template> \
    --subject "<email_subject>" \
    --name "<internal_campaign_name>"
```

#### Command Arguments Explained:
*   `--csv`: Path to your contact list file.
*   `--template`: Path to your markdown email body.
*   `--subject`: The subject line recipients will see (if not in template).
*   `--name`: A name for your own internal tracking (saved to database).
*   `--delay`: (Optional) Seconds to wait between emails to avoid spam filters (default is 10s).
*   `--dry-run`: (Optional) Use this flag to **test** without sending real emails.

---

## 6. Example Command (Copy & Paste)

Here is a full example you can run (assuming you have `test.csv` and `templates/software_engineer.md`):

```bash
python manage.py send_campaign \
    --csv test.csv \
    --template templates/software_engineer.md \
    --subject "Hello from Krishna" \
    --name "Test Campaign 1" \
    --delay 5
```

---

## 7. Troubleshooting

### "SMTPAuthenticationError" or "Username and Password not accepted"
*   **Cause**: Incorrect email or password in `.env`.
*   **Fix**: Double-check `EMAIL_HOST_USER`. Ensure you are using an **App Password** (not your login password) for Gmail.

### "Template file not found"
*   **Cause**: You typed the path wrong.
*   **Fix**: Ensure the file exists. If it's in a folder, include the folder name (e.g., `templates/my_file.md`).

### "CSV file not found"
*   **Cause**: The CSV file isn't where the command expects it to be.
*   **Fix**: Make sure you are in the root folder (where `manage.py` is) and the CSV is there too.

### "Skipping row with no email"
*   **Cause**: A row in your CSV is empty or missing the 'email' column.
*   **Fix**: Check your CSV for empty lines at the bottom.
