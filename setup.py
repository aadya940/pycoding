from setuptools import setup, find_packages

_dependencies = []
with open("requirements.txt", "r") as f:
    for line in f.readlines():
        _dependencies.append(line)

setup(
    name="pycoding",
    version="0.1.0",
    description="""An Agentic Python Library to create fully automated natural looking
    python coding tutorial generation with audio narration.""",
    author="Aadya Chinubhai",
    author_email="aadyachinubhai@gmail.com",
    packages=find_packages(),
    install_requires=_dependencies,
)
