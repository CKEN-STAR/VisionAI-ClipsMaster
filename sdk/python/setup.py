from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="clipsmaster-sdk",
    version="1.0.0",
    author="VisionAI Team",
    author_email="support@visionai.example.com",
    description="VisionAI-ClipsMaster API客户端SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/visionai/clipsmaster-sdk",
    project_urls={
        "Bug Tracker": "https://github.com/visionai/clipsmaster-sdk/issues",
        "Documentation": "https://visionai.example.com/docs/sdk/python/",
        "Source Code": "https://github.com/visionai/clipsmaster-sdk",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "typing-extensions>=4.0.0",
        "dataclasses>=0.8;python_version<'3.7'",
    ],
    keywords="video, ai, clips, editing, api, sdk",
) 