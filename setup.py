from setuptools import setup, find_packages

def get_long_description():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

packages = find_packages(include=["missmixed", "missmixed.*"])
print("Packages found:", packages)  # Debug print (helpful for you)

setup(
    name="missmixed",
    version="1.1.0",
    packages=packages,
    author="Mohammad Mahdi Kalhori",
    author_email="mohammad.mahdi.kalhor.99@gmail.com",
    maintainer="Mohammad Mahdi Kalhori, Fateme Akbari",
    maintainer_email="mohammad.mahdi.kalhor.99@gmail.com, fatemeeakbari.97@gmail.com",
    description="An Adaptive, Extensible and Configurable Multi-Layer Framework for Iterative Missing Value Imputation",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    keywords=['missing data', 'missing data imputation', 'machine learning', 'data science', 'preprocessing'],
    url="https://github.com/MohammadKlhr/missmixed",

    python_requires='>=3.10',
    install_requires=[
        'tqdm>=4.66',
        'pandas>=2.0.0',
        "numpy>=1.23",
        'scikit-learn>=1.4',
        'scipy>=1.6.0',
    ],
    extras_require={
        "ml": ["xgboost>=3.0"],
        "deep": ["tensorflow>=2.12"]
    },
    entry_points={
        'console_scripts': [
            'missmixed = missmixed.run:main',
        ],
    },
)