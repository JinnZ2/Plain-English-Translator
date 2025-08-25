from setuptools import setup, find_packages

with open(“README.md”, “r”, encoding=“utf-8”) as fh:
long_description = fh.read()

with open(“requirements.txt”, “r”, encoding=“utf-8”) as fh:
requirements = [line.strip() for line in fh if line.strip() and not line.startswith(”#”)]

setup(
name=“plain-english-translator”,
version=“1.0.0”,
author=“Plain English Translator Contributors”,
author_email=””,
description=“Translate complex medical, legal, insurance, and financial documents into plain English”,
long_description=long_description,
long_description_content_type=“text/markdown”,
url=“https://github.com/JinnZ2/Plain-English-Translator”,
project_urls={
“Bug Reports”: “https://github.com/JinnZ2/Plain-English-Translator/issues”,
“Source”: “https://github.com/JinnZ2/Plain-English-Translator”,
“Documentation”: “https://github.com/JinnZ2/Plain-English-Translator#readme”,
},
packages=find_packages(),
classifiers=[
“Development Status :: 4 - Beta”,
“Intended Audience :: End Users/Desktop”,
“Intended Audience :: Healthcare Industry”,
“Intended Audience :: Legal Industry”,
“Topic :: Text Processing :: Linguistic”,
“Topic :: Office/Business”,
“Topic :: Scientific/Engineering :: Medical Science Apps.”,
“License :: OSI Approved :: MIT License”,
“Programming Language :: Python :: 3”,
“Programming Language :: Python :: 3.7”,
“Programming Language :: Python :: 3.8”,
“Programming Language :: Python :: 3.9”,
“Programming Language :: Python :: 3.10”,
“Operating System :: OS Independent”,
],
python_requires=”>=3.7”,
install_requires=requirements,
extras_require={
“dev”: [
“pytest>=6.0”,
“black>=21.0”,
“flake8>=3.8”,
“pytest-cov>=2.10”,
],
},
entry_points={
“console_scripts”: [
“plain-english-translator=translator:main”,
“pet=translator:main”,  # Short alias
],
},
keywords=[
“medical”, “legal”, “insurance”, “translation”, “plain-language”,
“healthcare”, “patient-advocacy”, “accessibility”, “jargon”,
“consumer-protection”, “document-analysis”
],
include_package_data=True,
zip_safe=False,
)
