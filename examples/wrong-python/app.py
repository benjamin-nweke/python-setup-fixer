import tomllib

config = tomllib.loads('[app]\nname = "Python Setup Fixer demo"')
print(config['app']['name'])
