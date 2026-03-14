from __future__ import annotations
"""
Email Merge Tool - Send personalized emails via Gmail

Usage:
    # List emails in selected rows (preview without sending)
    python email_merge.py --sheet SHEET_ID --rows 3-10 --list
    
    # Using Google Sheets (recommended)
    python email_merge.py --sheet "https://docs.google.com/spreadsheets/d/SHEET_ID/edit" --template email_template.txt --rows 3-10
    python email_merge.py --sheet SHEET_ID --template email_template.txt --rows 1,3,5,7
    
    # Using local xlsx file
    python email_merge.py --xlsx contacts.xlsx --template email_template.txt --rows 3-10
    
    Add --dry-run to preview full email content without sending
"""

import argparse
import smtplib
import ssl
import re
import sys
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# SOCKS代理支持（仅在需要时启用）
SOCKS_AVAILABLE = False
try:
    import socks
    import socket as socket_module
    SOCKS_AVAILABLE = True
except ImportError:
    pass

# Google API imports
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


# Google Sheets API scope
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


# SMTP configurations for different email providers
SMTP_CONFIGS = {
    'gmail': {
        'server': 'smtp.gmail.com',
        'port': 465,
        'env_email': 'GMAIL_ADDRESS',
        'env_password': 'GMAIL_APP_PASSWORD'
    },
    'qq': {
        'server': 'smtp.qq.com',
        'port': 465,
        'env_email': 'QQ_EMAIL',
        'env_password': 'QQ_PASSWORD'
    },
    '163': {
        'server': 'smtp.163.com',
        'port': 465,
        'env_email': 'EMAIL_163',
        'env_password': 'PASSWORD_163'
    }
}


def load_config(account='gmail'):
    """Load email credentials from .env file"""
    load_dotenv()

    if account not in SMTP_CONFIGS:
        print(f"Error: Unknown account '{account}'")
        print(f"Available accounts: {', '.join(SMTP_CONFIGS.keys())}")
        sys.exit(1)

    config = SMTP_CONFIGS[account]
    email = os.getenv(config['env_email'])
    password = os.getenv(config['env_password'])

    if not email or not password:
        print(f"Error: {account} credentials not found!")
        print(f"Please add {config['env_email']} and {config['env_password']} to .env file")
        sys.exit(1)

    return email, password, config


def load_template(template_path: str) -> tuple[str, str]:
    """
    Load email template from file.
    First line should be 'subject: <subject line>'
    Rest is the email body.
    
    Returns: (subject, body)
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Extract subject from first line
    if lines[0].lower().startswith('subject:'):
        subject = lines[0].split(':', 1)[1].strip()
        body = '\n'.join(lines[1:]).strip()
    else:
        subject = "No Subject"
        body = content
    
    return subject, body


def get_google_sheets_credentials():
    """Get or refresh Google Sheets API credentials"""
    creds = None
    token_path = Path('token.json')
    credentials_path = Path('credentials.json')
    
    # Check if we have saved credentials
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                print("\nError: credentials.json not found!")
                print("\nTo use Google Sheets, you need to:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a new project (or select existing)")
                print("3. Enable 'Google Sheets API'")
                print("4. Go to 'Credentials' -> 'Create Credentials' -> 'OAuth client ID'")
                print("5. Choose 'Desktop app' as application type")
                print("6. Download the JSON and save as 'credentials.json' in this folder")
                sys.exit(1)
            
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    return creds


def extract_sheet_id(sheet_input: str) -> str:
    """Extract Google Sheets ID from URL or return as-is if already an ID"""
    # If it's a URL, extract the ID
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_input)
    if match:
        return match.group(1)
    
    # Otherwise assume it's already a sheet ID
    return sheet_input


def load_from_google_sheets(sheet_input: str, sheet_name: str = None) -> pd.DataFrame:
    """Load contacts from Google Sheets"""
    if not GOOGLE_API_AVAILABLE:
        print("Error: Google API libraries not installed.")
        print("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)
    
    sheet_id = extract_sheet_id(sheet_input)
    print(f"Connecting to Google Sheet: {sheet_id}")
    
    creds = get_google_sheets_credentials()
    service = build('sheets', 'v4', credentials=creds)
    
    # Get sheet metadata to find sheet names
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    
    if not sheets:
        print("Error: No sheets found in the spreadsheet")
        sys.exit(1)
    
    # Use first sheet if not specified
    if sheet_name is None:
        sheet_name = sheets[0]['properties']['title']
    
    print(f"Reading from sheet: '{sheet_name}'")
    
    # Get all data from the sheet
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{sheet_name}'"
    ).execute()
    
    values = result.get('values', [])
    
    if not values:
        print("Error: No data found in sheet")
        sys.exit(1)
    
    # First row is header
    headers = [str(h).lower().strip() for h in values[0]]
    
    # Create DataFrame from remaining rows
    data = []
    for row in values[1:]:
        # Pad row to match header length
        row_padded = row + [''] * (len(headers) - len(row))
        data.append(dict(zip(headers, row_padded)))
    
    df = pd.DataFrame(data)
    return df


def load_contacts(xlsx_path: str) -> pd.DataFrame:
    """Load contacts from xlsx file"""
    df = pd.read_excel(xlsx_path)
    
    # Normalize column names (lowercase, strip whitespace)
    df.columns = [str(col).lower().strip() for col in df.columns]
    
    return df


def parse_row_selection(row_spec: str, max_rows: int) -> list[int]:
    """
    Parse row selection string.
    
    Examples:
        "3-10" -> [3, 4, 5, 6, 7, 8, 9, 10]
        "1,3,5,7" -> [1, 3, 5, 7]
        "1-3,7,9-11" -> [1, 2, 3, 7, 9, 10, 11]
        None -> all rows
    
    Note: Row numbers are 1-based (matching Excel row numbers, excluding header)
    """
    if not row_spec:
        return list(range(1, max_rows + 1))
    
    rows = set()
    parts = row_spec.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            start, end = int(start), int(end)
            rows.update(range(start, end + 1))
        else:
            rows.add(int(part))
    
    # Filter valid rows and sort
    valid_rows = sorted([r for r in rows if 1 <= r <= max_rows])
    
    return valid_rows


def fill_template(template: str, row_data: dict) -> str:
    """
    Fill template placeholders with row data.
    Placeholders format: {{column_name}}
    """
    result = template
    
    # Find all placeholders
    placeholders = re.findall(r'\{\{(\w+)\}\}', template)
    
    for placeholder in placeholders:
        # Try to find matching column (case-insensitive)
        value = None
        placeholder_lower = placeholder.lower()
        
        for key, val in row_data.items():
            if key.lower() == placeholder_lower:
                value = val
                break
        
        # Handle NaN or missing values
        if value is None or (isinstance(value, float) and pd.isna(value)):
            value = f"[{placeholder}]"  # Keep placeholder visible if no data
        
        result = result.replace(f"{{{{{placeholder}}}}}", str(value))
    
    return result


def test_socks_proxy(host, port, timeout=2):
    """测试SOCKS5代理是否可用"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def find_available_proxy():
    """动态检测可用的SOCKS5代理端口"""
    # QuickQ常用端口放在前面优先检测
    common_ports = [10023, 10903, 10034, 1080, 1086, 7890, 7891, 8080, 9050]

    for port in common_ports:
        if test_socks_proxy('127.0.0.1', port):
            print(f"✓ 找到可用代理端口: {port}")
            return port

    return None


def send_email(
    sender_email: str,
    sender_password: str,
    recipient_email: str,
    subject: str,
    body: str,
    smtp_config: dict,
    dry_run: bool = False
) -> bool:
    """Send an email via SMTP with retry mechanism"""

    if dry_run:
        print(f"\n{'='*60}")
        print(f"[DRY RUN] Would send to: {recipient_email}")
        print(f"Subject: {subject}")
        print(f"{'='*60}")
        print(body)
        print(f"{'='*60}\n")
        return True

    # 重试机制：最多尝试3次
    max_retries = 3
    retry_delay = 10  # 秒

    for attempt in range(max_retries):
        try:
            # 仅为Gmail启用SOCKS代理
            original_socket = None
            if smtp_config['server'] == 'smtp.gmail.com' and SOCKS_AVAILABLE:
                # 动态查找可用代理端口
                proxy_port = find_available_proxy()

                if proxy_port is None:
                    raise Exception("未找到可用的SOCKS5代理端口。请检查梯子是否启动。")

                import socket
                original_socket = socket.socket
                socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', proxy_port)
                socket.socket = socks.socksocket
                print(f"✓ 已为Gmail启用SOCKS代理 (端口: {proxy_port})")

            try:
                # Create message
                message = MIMEMultipart("alternative")
                message["Subject"] = subject
                message["From"] = sender_email
                message["To"] = recipient_email

                # Add body as plain text
                part = MIMEText(body, "plain", "utf-8")
                message.attach(part)

                # Create secure SSL context
                context = ssl.create_default_context()

                # Send email using configured SMTP server
                with smtplib.SMTP_SSL(smtp_config['server'], smtp_config['port'], context=context) as server:
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, recipient_email, message.as_string())

                # 成功发送，返回True
                return True

            finally:
                # 恢复原始socket（如果修改过）
                if original_socket is not None:
                    import socket
                    socket.socket = original_socket

        except Exception as e:
            if attempt < max_retries - 1:
                # 还有重试机会
                print(f"⚠️  发送失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                # 最后一次尝试也失败了
                print(f"Error sending to {recipient_email}: {e}")
                return False

    return False


def get_email_from_row(row_data: dict) -> str | None:
    """Extract email address from row data"""
    # Try common email column names
    email_columns = ['email', 'e-mail', 'email address', 'mail', 'email_address']
    
    for col in email_columns:
        if col in row_data:
            email = row_data[col]
            if email and not (isinstance(email, float) and pd.isna(email)):
                email_str = str(email).strip()
                if email_str and '@' in email_str:
                    return email_str
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description='Email Merge Tool - Send personalized emails via Gmail',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # List emails in selected rows (no template needed)
    python email_merge.py --sheet SHEET_ID --rows 3-10 --list
    
    # Using Google Sheets
    python email_merge.py --sheet "https://docs.google.com/spreadsheets/d/SHEET_ID/edit" --template email_template.txt --rows 3-10
    python email_merge.py --sheet SHEET_ID --template email_template.txt --rows 1,3,5,7
    
    # Using local xlsx file  
    python email_merge.py --xlsx contacts.xlsx --template email_template.txt --rows 3-10
    python email_merge.py --xlsx contacts.xlsx --template email_template.txt --dry-run
        """
    )
    
    # Data source (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--xlsx', help='Path to xlsx file with contacts')
    source_group.add_argument('--sheet', help='Google Sheets URL or ID')
    
    parser.add_argument('--sheet-name', help='Specific sheet/tab name in Google Sheets (default: first sheet)')
    parser.add_argument('--template', help='Path to email template file (not required for --list)')
    parser.add_argument('--rows', help='Row selection (e.g., "3-10" or "1,3,5,7"). 1-based, excluding header.')
    parser.add_argument('--list', action='store_true', help='List emails in selected rows without sending')
    parser.add_argument('--dry-run', action='store_true', help='Preview emails without sending')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--delay', type=float, default=None, help='Delay between emails in seconds (default: auto based on account)')
    parser.add_argument('--account', default='gmail', choices=['gmail', 'qq', '163'],
                        help='Email account to use (default: gmail)')

    args = parser.parse_args()

    # 根据邮箱类型设置默认间隔
    if args.delay is None:
        if args.account == 'qq':
            args.delay = 8.0  # QQ邮箱间隔8秒，避免反垃圾机制
        else:
            args.delay = 2.0  # Gmail和163邮箱间隔2秒

    # For list mode, template is not required
    if not args.list and not args.template:
        parser.error("--template is required unless using --list")
    
    # Load contacts from Google Sheets or xlsx first (for --list mode)
    if args.sheet:
        print(f"Connecting to Google Sheets...")
        df = load_from_google_sheets(args.sheet, args.sheet_name)
    else:
        print(f"Loading contacts from: {args.xlsx}")
        df = load_contacts(args.xlsx)

    print(f"Found {len(df)} contacts")
    print(f"Columns: {list(df.columns)}")

    # ============================================================
    # 🛡️ PRE-SEND HOOK: 强制执行黑名单检查
    # ============================================================
    if not args.list and not args.dry_run and args.xlsx:
        import subprocess
        hook_script = Path(__file__).parent / 'pre_send_hook.py'
        if hook_script.exists():
            print(f"\n执行pre-send hook检查...")
            result = subprocess.run(
                ['python3', str(hook_script), args.xlsx],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.returncode != 0:
                print(result.stderr)
                print("\n❌ Pre-send hook检查失败，终止发送")
                sys.exit(1)
        else:
            print(f"\n⚠️  警告: pre_send_hook.py不存在，跳过hook检查")

    # Parse row selection
    selected_rows = parse_row_selection(args.rows, len(df))
    
    # List mode - just show emails and exit
    if args.list:
        print(f"\n{'='*60}")
        print(f"EMAILS IN SELECTED ROWS ({len(selected_rows)} rows)")
        print(f"{'='*60}")
        
        valid_count = 0
        for row_num in selected_rows:
            row_idx = row_num - 1
            row_data = df.iloc[row_idx].to_dict()
            email = get_email_from_row(row_data)
            name = row_data.get('name', '')
            
            if email:
                print(f"  Row {row_num:3d}: {email:<40} ({name})")
                valid_count += 1
            else:
                print(f"  Row {row_num:3d}: [NO EMAIL]")
        
        print(f"{'='*60}")
        print(f"Total: {len(selected_rows)} rows, {valid_count} valid emails")
        sys.exit(0)
    
    # ============================================================
    # 最高优先级：检查黑名单，绝对不可重复触达
    # ============================================================
    blacklist_file = 'data/sent_emails_blacklist.txt'
    if not os.path.exists(blacklist_file):
        print(f"\n{'='*60}")
        print("错误：找不到黑名单文件！")
        print(f"文件路径: {blacklist_file}")
        print("请先运行脚本生成黑名单文件")
        print(f"{'='*60}")
        sys.exit(1)

    with open(blacklist_file, 'r', encoding='utf-8') as f:
        blacklist = set(line.strip() for line in f if line.strip())

    print(f"\n{'='*60}")
    print(f"✓ 已加载黑名单: {len(blacklist)} 个已发送邮箱")
    print(f"{'='*60}")

    # 检查当前批次是否有重复
    duplicate_emails = []
    for row_num in selected_rows:
        row_idx = row_num - 1
        row_data = df.iloc[row_idx].to_dict()
        email = get_email_from_row(row_data)
        if email and email in blacklist:
            duplicate_emails.append((row_num, email))

    if duplicate_emails:
        print(f"\n{'='*60}")
        print("❌ 错误：发现重复邮箱！绝对不可重复触达！")
        print(f"{'='*60}")
        for row_num, email in duplicate_emails:
            print(f"  Row {row_num}: {email}")
        print(f"{'='*60}")
        print(f"共发现 {len(duplicate_emails)} 个重复邮箱")
        print("已终止发送，请检查数据源")
        print(f"{'='*60}")
        sys.exit(1)

    print(f"✓ 黑名单检查通过：无重复邮箱\n")

    # Load configuration (only needed for sending)
    sender_email, sender_password, smtp_config = load_config(args.account)

    # Load template
    print(f"\nLoading template from: {args.template}")
    subject_template, body_template = load_template(args.template)
    print(f"Subject: {subject_template}")

    print(f"\nSelected rows: {selected_rows}")
    print(f"Total emails to send: {len(selected_rows)}")
    
    if args.dry_run:
        print("\n*** DRY RUN MODE - No emails will be sent ***")

    # Confirm before sending
    if not args.dry_run and not args.yes:
        confirm = input(f"\nReady to send {len(selected_rows)} emails. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    # Process each selected row
    success_count = 0
    fail_count = 0
    skipped_count = 0
    
    for i, row_num in enumerate(selected_rows):
        # DataFrame is 0-indexed, row numbers are 1-indexed
        row_idx = row_num - 1
        row_data = df.iloc[row_idx].to_dict()
        
        # Get recipient email
        recipient_email = get_email_from_row(row_data)
        
        if not recipient_email:
            print(f"[Row {row_num}] Skipped - No email address found")
            skipped_count += 1
            continue
        
        # Fill template
        subject = fill_template(subject_template, row_data)
        body = fill_template(body_template, row_data)
        
        # Send email
        print(f"[Row {row_num}] Sending to: {recipient_email}")

        if send_email(sender_email, sender_password, recipient_email, subject, body, smtp_config, args.dry_run):
            success_count += 1
        else:
            fail_count += 1
        
        # Delay between emails (except for last one)
        if not args.dry_run and i < len(selected_rows) - 1:
            time.sleep(args.delay)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total selected: {len(selected_rows)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Skipped (no email): {skipped_count}")

    # ============================================================
    # Post-send Hook: 自动更新黑名单并删除中间文件
    # ============================================================
    if not args.dry_run and args.xlsx:
        if fail_count > 0:
            # 有失败，停下来报告
            print(f"\n{'='*60}")
            print("⚠️  有邮件发送失败，不自动更新黑名单")
            print("请手动处理失败的邮件")
            print(f"{'='*60}")
            sys.exit(1)
        else:
            # 全部成功，调用Post-send Hook
            import subprocess
            hook_script = Path(__file__).parent / 'post_send_hook.py'
            if hook_script.exists():
                result = subprocess.run(
                    ['python3', str(hook_script), args.xlsx],
                    capture_output=True,
                    text=True
                )
                print(result.stdout)
                if result.returncode != 0:
                    print(result.stderr)
                    print("\n❌ Post-send hook执行失败")
                    sys.exit(1)
            else:
                print(f"\n⚠️  警告: post_send_hook.py不存在，跳过自动更新黑名单")


if __name__ == '__main__':
    main()
