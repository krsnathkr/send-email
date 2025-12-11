# How to Run the Email Campaign

This guide explains how to execute the bulk email campaign command.

## The Command

To run the campaign, execute the following command in your terminal from the project root:

```bash
venv/bin/python manage.py send_campaign --csv test.csv --template templates/machine_learning_engineer.md --subject "Applying for Machine Learning Engineer Role" --name "ML Campaign"
```

## Component Breakdown

Here is a detailed explanation of each part of the command:

### 1. The Python Interpreter
`venv/bin/python`
*   **What it is**: This points to the Python executable inside your virtual environment (`venv`).
*   **Why use it**: Using the virtual environment's Python ensures that the command runs with all the correct dependencies (like Django) installed for this project, rather than your system-wide Python.

### 2. The Django Manager
`manage.py`
*   **What it is**: The standard Django command-line utility.
*   **Why use it**: It acts as the gateway to interact with your Django project (e.g., running servers, database migrations, or custom commands).

### 3. The Custom Command
`send_campaign`
*   **What it is**: The name of the custom management command built for this project (located in `emails/management/commands/send_campaign.py`).
*   **What it does**: It triggers the logic to read the CSV, parse the template, and start sending emails.

### 4. Arguments & Flags

`--csv test.csv`
*   **Purpose**: Specifies the source of your recipient data.
*   **Details**: usage of `test.csv` means the script will look for a file named `test.csv` in the current directory. This file must contain columns like `email`, `first_name`, etc., which are used to personalize the email.

`--template templates/machine_learning_engineer.md`
*   **Purpose**: Specifies the content of the email.
*   **Details**: Points to the Markdown file that contains the email body. The script converts this Markdown into HTML for the email content. placeholders like `[first_name]` in this file will be replaced by data from the CSV.

`--subject "Applying for Machine Learning Engineer Role"`
*   **Purpose**: Sets the subject line of the email.
*   **Details**: This string will appear as the subject in the recipient's inbox. Note: If the template file itself has a `Subject:` line at the top, that will take precedence over this flag.

`--name "ML Campaign"`
*   **Purpose**: Identifies the campaign internally.
*   **Details**: This name is stored in your database (in the `EmailCampaign` table). It helps you group and track logs (sent/failed emails) for this specific batch of emails.

## Additional Options

*   **Dry Run**: Add `--dry-run` to the end of the command to simulate sending without actually sending emails. This is useful for checking if your template renders correctly.
    ```bash
    ... --name "ML Campaign" --dry-run
    ```
*   **Delay**: Add `--delay <seconds>` to change the waiting time between emails (default is 10 seconds).
    ```bash
    ... --name "ML Campaign" --delay 5
    ```
