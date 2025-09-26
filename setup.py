import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    require = fh.readlines()
require= [x.strip() for x in require]

setuptools.setup(
    name="pySankey",
    version="0.1.0.replication",
    author="anazalea",
    author_email="anneyagolob@gmail.com",
    description="Fork of pySankey with formatting enhancements for academic replication",
    long_description=long_description,
    license='GNU General Public License v3.0',
    long_description_content_type="text/markdown",
    url="https://github.com/vasudeva-ram/pySankey",
    packages=setuptools.find_packages(),
    install_requires=require,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
