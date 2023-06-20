import subprocess

HERE_DOCUMENT = \
"""sleep 3
echo done"""

execution = "bash <<-END\n" + HERE_DOCUMENT + "\nEND"
p = subprocess.Popen(execution, shell=True) 
p.wait()
