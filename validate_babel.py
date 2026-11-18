import re
import subprocess
import os

with open('web/index.html', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'<script type="text/babel">(.*?)</script>', content, re.DOTALL)
if m:
    with open('test_jsx.js', 'w', encoding='utf-8') as out:
        out.write(m.group(1))
    print('JSX script length:', len(m.group(1)))
    
    # Run node babel validation
    node_script = """
    const fs = require('fs');
    const code = fs.readFileSync('test_jsx.js', 'utf8');
    const babel = require('@babel/standalone');
    try {
        const res = babel.transform(code, { presets: ['react'] });
        console.log('TRANSPILE SUCCESS! Output length:', res.code.length);
    } catch(err) {
        console.error('TRANSPILE ERROR:', err.message);
        process.exit(1);
    }
    """
    with open('run_check.js', 'w', encoding='utf-8') as nout:
        nout.write(node_script)
    res = subprocess.run(['node', 'run_check.js'], capture_output=True, text=True)
    print(res.stdout)
    print(res.stderr)
    os.remove('test_jsx.js')
    os.remove('run_check.js')
else:
    print('Script tag not found')

