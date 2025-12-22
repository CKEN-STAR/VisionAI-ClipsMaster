import sys, subprocess
print('Installing httpx via pip...')
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'httpx>=0.27.0'])
print('Done.')

