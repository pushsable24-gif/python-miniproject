from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# termcolor for terminal colors
from termcolor import colored as tc_colored

# ------------------------ Terminal color helper ------------------------
def colored(text, color_name):
    # map your old "purple" to termcolor's "magenta"
    mapping = {
        'purple': 'magenta'
    }
    return tc_colored(str(text), mapping.get(color_name, color_name))

# ------------------------ Helpers ------------------------

def safe_float(prompt):
    while True:
        try:
            val = input(prompt).strip().replace(',', '')
            f = float(val)
            if f < 0:
                print(colored('Please enter a non-negative number.', 'red'))
                continue
            return f
        except ValueError:
            print(colored('Invalid number — try again.', 'red'))


def safe_int(prompt):
    while True:
        try:
            val = int(input(prompt).strip())
            if val < 0:
                print(colored('Enter a non-negative integer.', 'red'))
                continue
            return val
        except ValueError:
            print(colored('Invalid integer — try again.', 'red'))


def parse_date(s):
    s = s.strip()
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d %b %Y', '%d %B %Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    try:
        d = int(s)
        today = datetime.today()
        return datetime(today.year, today.month, d).date()
    except Exception:
        return None

# ------------------------ Data collection ------------------------
print('\n' + colored("Welcome to Smart Monthly Budget Optimizer💸💸(Student Edition)", 'green') + '\n')

monthly_budget = safe_float(colored("Enter your monthly pocket money 💰 (₹): ", 'cyan'))
entries_count = safe_int(colored("How many spending entries do you want to enter?: ", 'yellow'))

rows = []
print('\n' + colored("Enter each spending entry. For date you can use YYYY-MM-DD or DD-MM-YYYY or just day number", 'blue'))
for i in range(entries_count):
    print('\n' + colored(f'Entry {i+1} —', 'purple'))
    while True:
        ds = input(colored("  Date📆: ", 'cyan'))
        d = parse_date(ds)
        if d is None:
            print(colored("  ❎Couldn't parse date. Try again!! (e.g. 2025-11-25 or 25-11-2025 or 25).", 'red'))
            continue
        break
    amt = safe_float(colored("  Amount spent 🪙  (₹): ", 'cyan'))
    cat = input(colored("  Category (food, travel, recharge, snacks, fees, others, etc.): ", 'yellow')).strip().lower() or 'others'
    note = input(colored("  Short note/merchant (optional): ", 'blue')).strip()
    rows.append({'date': d, 'amount': amt, 'category': cat, 'note': note})

if len(rows) == 0:
    print(colored("No entries provided — exiting.", 'red'))
# ------------------------ Build DataFrame ------------------------

df = pd.DataFrame(rows)
df.sort_values(by='date', inplace=True)
df['category'] = df['category'].str.strip().replace('', 'others')

# ------------------------ Tabular output (properly aligned) ------------------------
print('\n' + colored('Your spending table (first rows):', 'purple') + '\n')

# Prepare plain strings to compute widths
date_strs = [str(d) for d in df['date']]
amount_strs = [f"₹{a:.2f}" for a in df['amount']]
cat_strs = [str(c) for c in df['category']]
note_strs = [str(n) if n else '-' for n in df['note']]

date_width = max(len("date"), *(len(s) for s in date_strs))
amount_width = max(len("amount"), *(len(s) for s in amount_strs))
cat_width = max(len("category"), *(len(s) for s in cat_strs))
note_width = max(len("note"), *(len(s) for s in note_strs))

# Header (pad first, then color)
h_date = colored(f"{'date':<{date_width}}", 'cyan')
h_amount = colored(f"{'amount':>{amount_width}}", 'yellow')
h_cat = colored(f"{'category':<{cat_width}}", 'green')
h_note = colored(f"{'note':<{note_width}}", 'blue')

print(f"{h_date}  {h_amount}  {h_cat}  {h_note}")

# Rows
for i, r in enumerate(df.itertuples(index=False)):
    date_plain = f"{str(r.date):<{date_width}}"
    amt_plain = f"{amount_strs[i]:>{amount_width}}"
    cat_plain = f"{str(r.category):<{cat_width}}"
    note_plain = f"{note_strs[i]:<{note_width}}"

    date_s = colored(date_plain, 'cyan')
    amt_s = colored(amt_plain, 'yellow')
    cat_s = colored(cat_plain, 'green')
    note_s = colored(note_plain, 'blue')

    print(f"{date_s}  {amt_s}  {cat_s}  {note_s}")

# ------------------------ Summary info ------------------------
print('\n' + colored('Summary info:', 'purple'))
print(f" {colored('Total entries:', 'blue')} {colored(len(df), 'yellow')}")
print(f" {colored('Monthly pocket money:', 'blue')} {colored('₹{:.2f}'.format(monthly_budget), 'cyan')}")
print(
    f" {colored('Total spent (sum of entries):', 'blue')} "
    f"{colored('₹{:.2f}'.format(df['amount'].sum()), 'green' if df['amount'].sum() <= monthly_budget else 'red')}"
)

# ------------------------ Analysis ------------------------

total_spent = df['amount'].sum()
remaining = monthly_budget - total_spent

cat_summary = df.groupby('category', as_index=False)['amount'].sum().sort_values(by='amount', ascending=False)
cat_summary['percent'] = (100 * cat_summary['amount'] / total_spent) if total_spent > 0 else 0

suggestions = []
for _, row in cat_summary.iterrows():
    cat = row['category']
    amt = row['amount']
    pct = row['percent'] if total_spent > 0 else 0
    if pct >= 30:
        cut = amt * 0.25
        suggestions.append((cat, cut, 'high'))
    elif pct >= 15:
        cut = amt * 0.15
        suggestions.append((cat, cut, 'medium'))
    elif pct >= 7:
        cut = amt * 0.08
        suggestions.append((cat, cut, 'small'))

# longest overspend streak
daily_budget = monthly_budget / 30.0
daily = df.groupby('date', as_index=False)['amount'].sum().sort_values('date')
daily['overspend'] = daily['amount'] > daily_budget
longest = 0
current = 0
for v in daily['overspend']:
    if v:
        current += 1
        longest = max(longest, current)
    else:
        current = 0

# ------------------------ Print analysis ------------------------
print('\n' + colored('Category-wise spending (descending):', 'purple'))
for _, r in cat_summary.iterrows():
    print(
        f" {colored(r['category'], 'green'):<12} "
        f"{colored('₹{:.2f}'.format(r['amount']), 'yellow'):>12}  "
        f"{colored('{:.2f}%'.format(r['percent']), 'cyan'):>8}"
    )

print('\n' + colored('Quick analysis & tips:', 'purple'))
if remaining >= 0:
    print(colored(f" You're within your monthly pocket money. Remaining savings: ₹{remaining:.2f}", 'green') + '  ' + colored('💰', 'yellow'))
else:
    print(colored(f" You've overspent by ₹{abs(remaining):.2f}. Consider trimming expenses!", 'red') + '  ' + colored('😬', 'yellow'))

if suggestions:
    print('\n' + colored('Top saving suggestions📒 (estimates):', 'purple'))
    for cat, cut, level in suggestions:
        emoji = '🔥' if level == 'high' else ('⚠️' if level == 'medium' else '✨')
        color = 'red' if level == 'high' else ('yellow' if level == 'medium' else 'cyan')
        print(f"  {emoji} {colored('Reduce', color)} {colored(cat, 'green')} by ~{colored('₹{:.0f}'.format(cut), color)} per month (~{level} leak).")
else:
    print(colored('  Great — no obvious big leaks detected. Keep it up!', 'green'))

print(colored(f"Longest overspending streak (days in a row with spend > daily budget ₹{daily_budget:.2f}): {longest} days", 'blue'))

potential_savings = sum(cut for _, cut, _ in suggestions)
predicted_savings = max(0.0, remaining + potential_savings)
print(colored(f"If you apply suggested cuts, you could potentially save an extra: ₹{potential_savings:.2f}.", 'yellow'))
print(colored(f"Estimated total savings this month (current + suggested cuts): ₹{predicted_savings:.2f}", 'green'))

# ------------------------ Visualization ------------------------
cats = cat_summary['category'].tolist()
vals = cat_summary['amount'].values
if len(cats) > 0:
    plt.figure(figsize=(9, 5))
    cmap = plt.get_cmap('tab20')
    bar_colors = [cmap(i % cmap.N) for i in range(len(cats))]
    bars = plt.bar(cats, vals, color=bar_colors)
    plt.title('Spending by Category')
    plt.xlabel('Category')
    plt.ylabel('Amount (₹)')
    plt.xticks(rotation=45, ha='right')
    for bar in bars:
        h = bar.get_height()
        plt.annotate(
            f'₹{h:.0f}',
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 5),
            textcoords='offset points',
            ha='center'
        )
    plt.tight_layout()
    plt.savefig('spending_by_category.png', dpi=150)
    print(colored('Saved bar chart as spending_by_category.png', 'cyan'))

# Pie chart: expenditures vs savings (or overspent)
spent = total_spent
savings = remaining if remaining > 0 else 0
overspent = abs(remaining) if remaining < 0 else 0

labels = []
sizes = []
colors_pie = []
if savings > 0:
    labels = ['Spent', 'Savings']
    sizes = [spent, savings]
    colors_pie = ['#ff9999', '#99ff99']
else:
    labels = ['Spent', 'Overspent']
    sizes = [spent, overspent]
    colors_pie = ['#ff9999', '#ffcc99']

if sum(sizes) > 0:
    plt.figure(figsize=(6, 6))
    plt.pie(
        sizes,
        labels=labels,
        autopct=lambda pct: f"{pct:.1f}%(₹{int(round(pct/100*sum(sizes))):,})",
        startangle=90,
        colors=colors_pie,
        wedgeprops={'edgecolor': 'white'}
    )
    plt.title('Expenditures vs Savings')
    plt.tight_layout()
    plt.savefig('spending_vs_savings_pie.png', dpi=150)
    print(colored('Saved pie chart as spending_vs_savings_pie.png', 'cyan'))

print('\n' + colored('Category percentages (text style):', 'purple'))
for _, r in cat_summary.iterrows():
    print(
        f"  {colored(r['category'], 'green')}: "
        f"{colored('₹{:.2f}'.format(r['amount']), 'yellow')} "
        f"({colored('{:.1f}%'.format(r['percent']), 'cyan')})"
    )

print('\n' + colored('Pro tip: Track daily for a week and reduce the top 1-2 leaking categories by 10-25%. Small steps win!', 'blue'))
print('\n' + colored('Thanks for using Smart Monthly Budget Optimizer — Good luck!', 'green'))

plt.show()
pass