from rich.table import Table
from rich.console import Console

table = Table('Project', 'Status')
table.add_row('Python Setup Fixer demo', 'Ready')
Console().print(table)
