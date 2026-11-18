import glob, os, shutil, subprocess, sys, zipfile
# the dataset may arrive unzipped or as the zip itself; handle both
hits = glob.glob('/kaggle/input/**/scripts/compare_jica.py', recursive=True)
os.makedirs('/kaggle/working/proj', exist_ok=True)
if hits:
    shutil.copytree(os.path.dirname(os.path.dirname(hits[0])), '/kaggle/working/proj', dirs_exist_ok=True)
else:
    zips = glob.glob('/kaggle/input/**/kathmandu_sim_h1h7.zip', recursive=True)
    assert zips, 'project not found under /kaggle/input'
    zipfile.ZipFile(zips[0]).extractall('/kaggle/working/proj')
os.chdir('/kaggle/working/proj')
print(os.listdir('.'), flush=True)
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'uxsim==1.14.2', 'networkx', 'osmnx'], check=True)
for attempt in range(3):   # resumable: a killed worker (e.g. out of memory) only loses its own run
    r = subprocess.run([sys.executable, '-u', 'scripts/project_jica.py', '--first-seed', '1', '--seeds', '8',
                    '--jobs', '3'], check=False)
    if r.returncode == 0:
        break
shutil.copy('results/jica_projection.partial.csv', '/kaggle/working/jica_projection_seeds1-8.csv')
print('saved /kaggle/working/jica_projection_seeds1-8.csv', flush=True)
