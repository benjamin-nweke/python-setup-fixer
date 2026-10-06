"""Sample project created for testing Python Setup Fixer. Fictional data only."""
import csv
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path


def main():
    try:
        source = os.environ['EXPENSE_DEMO_CSV']
    except KeyError:
        raise SystemExit('Missing required configuration: EXPENSE_DEMO_CSV. Set it to expenses.csv for the included fictional data.')
    path = Path(source)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    totals = {}
    count = 0
    try:
        with path.open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            if not {'category', 'amount'}.issubset(reader.fieldnames or []):
                raise ValueError('CSV needs category and amount columns')
            for row in reader:
                category = (row['category'] or '').strip()
                amount = Decimal(row['amount'])
                if not category or not amount.is_finite() or amount < 0:
                    raise ValueError('Each expense needs a category and a finite, nonnegative amount')
                totals[category] = totals.get(category, Decimal('0')) + amount
                count += 1
    except (OSError, ValueError, TypeError, InvalidOperation, csv.Error) as exc:
        raise SystemExit('Could not read expense data: ' + str(exc))
    print('EXPENSE DEMO | Fictional data | Amounts in sample units')
    print('Sample project created for testing Python Setup Fixer')
    print('Records: ' + str(count))
    for category, amount in sorted(totals.items()):
        print(f'{category:<16} {amount:>10.2f}')
    print(f'{"TOTAL":<16} {sum(totals.values(), Decimal("0")):>10.2f}')


if __name__ == '__main__':
    main()
