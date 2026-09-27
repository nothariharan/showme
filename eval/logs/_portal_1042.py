import sys, os, time
sys.path.insert(0, 'examples/billing_portal')
import server
from pathlib import Path
d = Path('eval/logs/dl-1042')
d.mkdir(parents=True, exist_ok=True)
h = server.start(d)
port = h.server_address[1]
with open('eval/logs/portal-1042-port.txt', 'w') as f:
    f.write(str(port))
    f.flush()
print(port, flush=True)
time.sleep(3600)
