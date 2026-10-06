# Expense demo

Sample project created for testing Python Setup Fixer. The code and fictional CSV rows were created for this demonstration, without copying an external repository or dataset. This is a controlled fixture, not an independent real-world benchmark or a separately branded product.

It reads a CSV file and prints totals by category. It uses only Python's standard library, runs offline, and does not modify the input file.

The deliberate setup problem is an unset `EXPENSE_DEMO_CSV` environment variable. The variable selects the input file. `.env.example` documents it but is not loaded automatically.

From this folder:

```sh
python3 app.py
EXPENSE_DEMO_CSV=expenses.csv python3 app.py
```

The first command fails when the variable is unset. The second prints six records, Food 20.00, Supplies 18.00, Transport 12.00, and TOTAL 50.00 in fictional sample units.

In Python Setup Fixer, select **Expense demo** and check the project. Run verification. The first failed verification becomes the baseline automatically when the current baseline has no command result. Expand **Configuration for this session**, select **Use included expense data**, and run verification again. This sets the input path for the session only. It does not install packages or edit project files.
