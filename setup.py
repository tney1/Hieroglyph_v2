from setuptools import setup, find_packages

print(f"SETTING UP HIEROGLYPH, packages: {find_packages('src')}")

setup(name='hieroglyph',
      version=open('VERSION').read().strip(),
      python_requires='>=3.6',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      install_requires=[line.strip() for line in open('requirements.txt').readlines() if line.strip() and '#' not in line.strip()]
)
