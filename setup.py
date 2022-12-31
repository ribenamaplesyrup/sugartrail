from setuptools import setup, find_packages

with open("config/requirements.txt") as requirement_file:
    requirements = requirement_file.read().split()

setup(
    name="sugartrail",
    version="1.0.0",
    install_requires=requirements,
    packages=find_packages(exclude=["notebooks", "dashboard", "assets"]),
)
