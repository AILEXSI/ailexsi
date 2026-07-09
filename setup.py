from setuptools import setup, find_packages

setup(
    name="ailexsi",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["pydantic", "sqlalchemy"],
    description="The Continuity Layer for AI Systems",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="AILEXSI",
    author_email="ceo@ailexsi.com",
    url="https://github.com/AILEXSI/ailexsi",
    license="MIT",
)