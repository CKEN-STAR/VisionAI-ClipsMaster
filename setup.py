from setuptools import setup, find_packages

setup(
    name="visionai-clipsmaster",
    version="1.0.1",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0.1",
        "loguru>=0.7.2",
        "numpy>=1.24.0",
        "pandas>=2.2.0",
        "tqdm>=4.65.0",
        "python-dotenv>=1.0.0",
        "Pillow>=10.0.0",
        "psutil>=5.9.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "mypy>=1.7.1",
            "flake8>=6.1.0",
            "pre-commit>=3.5.0",
        ],
    },
    python_requires=">=3.8",
) 