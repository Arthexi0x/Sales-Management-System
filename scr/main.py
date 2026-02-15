+"""Simple CLI Sales Management System.
+
+Features:
+- Password protected login (admin)
+- Load previous sales data from file
+- Add sales entries
+- View all sales entries
+- Show daily total sales
+- Generate sales report
+- Save sales data to file
+"""
+
+from __future__ import annotations
+
+from collections import defaultdict
+from datetime import datetime
+import json
+import os
+from pathlib import Path
+from statistics import mean
+from typing import Any
+
+DATA_FILE = Path(__file__).resolve().parent / "sales_data.json"
+REPORTS_DIR = Path(__file__).resolve().parent / "reports"
+DEFAULT_ADMIN_PASSWORD = "admin123"
+MAX_LOGIN_ATTEMPTS = 3
+
+
+def get_admin_password() -> str:
+    """Read admin password from environment with a safe fallback."""
+    return os.getenv("SMS_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
+
+
+def load_sales_data() -> list[dict[str, Any]]:
+    """Load sales data from disk, returning an empty list on first run."""
+    if not DATA_FILE.exists():
+        return []
+
+    try:
+        with DATA_FILE.open("r", encoding="utf-8") as file:
+            data = json.load(file)
+            return data if isinstance(data, list) else []
+    except (json.JSONDecodeError, OSError):
+        return []
+
+
+def save_sales_data(sales: list[dict[str, Any]]) -> None:
+    """Persist sales data to disk."""
+    with DATA_FILE.open("w", encoding="utf-8") as file:
+        json.dump(sales, file, indent=2)
+
+
+def parse_sale_record(record: dict[str, Any]) -> tuple[datetime, float] | None:
+    """Return parsed record or None if invalid."""
+    try:
+        timestamp = str(record["timestamp"])
+        amount = float(record["amount"])
+        parsed_time = datetime.fromisoformat(timestamp)
+        return parsed_time, amount
+    except (KeyError, TypeError, ValueError):
+        return None
+
+
+def authenticate() -> bool:
+    """Password-based authentication for admin access with retries."""
+    print("\n=== Sales Management Login ===")
+    admin_password = get_admin_password()
+
+    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
+        password = input("Enter admin password: ").strip()
+        if password == admin_password:
+            print("Login successful.\n")
+            return True
+
+        attempts_left = MAX_LOGIN_ATTEMPTS - attempt
+        if attempts_left > 0:
+            print(f"Invalid password. Attempts left: {attempts_left}")
+
+    print("Access denied. Too many failed attempts.")
+    return False
+
+
+def add_sale(sales: list[dict[str, Any]]) -> None:
+    """Prompt for a sales amount and append a record."""
+    amount_text = input("Enter sale amount: ").strip()
+
+    try:
+        amount = float(amount_text)
+        if amount < 0:
+            raise ValueError
+    except ValueError:
+        print("Invalid amount. Please enter a non-negative number.")
+        return
+
+    sales.append(
+        {
+            "amount": amount,
+            "timestamp": datetime.now().isoformat(timespec="seconds"),
+        }
+    )
+    save_sales_data(sales)
+    print(f"Sale of {amount:.2f} added successfully.")
+
+
+def view_sales(sales: list[dict[str, Any]]) -> None:
+    """Display all sales entries."""
+    if not sales:
+        print("No sales records found.")
+        return
+
+    print("\n=== Sales Records ===")
+    displayed = 0
+    for index, record in enumerate(sales, start=1):
+        parsed = parse_sale_record(record)
+        if parsed is None:
+            print(f"{index}. Invalid record skipped")
+            continue
+
+        sale_time, amount = parsed
+        displayed += 1
+        print(
+            f"{index}. Amount: {amount:.2f} | "
+            f"Time: {sale_time.strftime('%Y-%m-%d %H:%M:%S')}"
+        )
+
+    if displayed == 0:
+        print("No valid sales records to display.")
+
+
+def show_daily_total(sales: list[dict[str, Any]]) -> None:
+    """Show total sales for the current date."""
+    today = datetime.now().date()
+    total = 0.0
+
+    for record in sales:
+        parsed = parse_sale_record(record)
+        if parsed is None:
+            continue
+
+        sale_time, amount = parsed
+        if sale_time.date() == today:
+            total += amount
+
+    print(f"Today's total sales: {total:.2f}")
+
+
+def generate_sales_report(sales: list[dict[str, Any]]) -> None:
+    """Generate summary report on screen and save it to file."""
+    valid_sales: list[tuple[datetime, float]] = []
+    for record in sales:
+        parsed = parse_sale_record(record)
+        if parsed is not None:
+            valid_sales.append(parsed)
+
+    if not valid_sales:
+        print("No valid sales records found. Report was not generated.")
+        return
+
+    amounts = [amount for _, amount in valid_sales]
+    total_sales = sum(amounts)
+    average_sale = mean(amounts)
+    max_sale = max(amounts)
+    min_sale = min(amounts)
+
+    grouped_by_day: dict[str, float] = defaultdict(float)
+    for sale_time, amount in valid_sales:
+        grouped_by_day[sale_time.strftime("%Y-%m-%d")] += amount
+
+    report_lines = [
+        "=== Sales Report ===",
+        f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
+        f"Total Records: {len(valid_sales)}",
+        f"Total Sales: {total_sales:.2f}",
+        f"Average Sale: {average_sale:.2f}",
+        f"Highest Sale: {max_sale:.2f}",
+        f"Lowest Sale: {min_sale:.2f}",
+        "",
+        "Daily Totals:",
+    ]
+
+    for day in sorted(grouped_by_day):
+        report_lines.append(f"- {day}: {grouped_by_day[day]:.2f}")
+
+    report_text = "\n".join(report_lines)
+    print(f"\n{report_text}")
+
+    REPORTS_DIR.mkdir(exist_ok=True)
+    report_name = datetime.now().strftime("sales_report_%Y%m%d_%H%M%S.txt")
+    report_path = REPORTS_DIR / report_name
+    with report_path.open("w", encoding="utf-8") as report_file:
+        report_file.write(report_text + "\n")
+
+    print(f"Report saved to: {report_path}")
+
+
+def menu_loop() -> None:
+    """Display menu and handle user actions."""
+    sales = load_sales_data()
+
+    while True:
+        print("\n=== Admin Dashboard ===")
+        print("1. Add Sale")
+        print("2. View Sales")
+        print("3. Show Daily Total")
+        print("4. Generate Sales Report")
+        print("5. Exit")
+
+        choice = input("Choose an option (1-5): ").strip()
+
+        if choice == "1":
+            add_sale(sales)
+        elif choice == "2":
+            view_sales(sales)
+        elif choice == "3":
+            show_daily_total(sales)
+        elif choice == "4":
+            generate_sales_report(sales)
+        elif choice == "5":
+            print("Exiting Sales Management System. Goodbye!")
+            break
+        else:
+            print("Invalid choice. Please select 1, 2, 3, 4, or 5.")
+
+
+def main() -> None:
+    """Entry point."""
+    if authenticate():
+        menu_loop()
+
+
+if __name__ == "__main__":
+    main()
 
EOF
)

