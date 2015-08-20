from tabulate import tabulate

test = [['pennytal',5],['boobity', 123],['goood', 4]]
print(test)
print(tabulate(test, headers=['trunk', 'num']))