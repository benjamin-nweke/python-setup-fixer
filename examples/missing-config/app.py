import os

try:
    endpoint = os.environ['FIXER_DEMO_ENDPOINT']
except KeyError:
    raise SystemExit('Missing required configuration: FIXER_DEMO_ENDPOINT')
print('Demo started successfully. Configuration is present.')
