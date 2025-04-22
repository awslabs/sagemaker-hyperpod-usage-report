from setuptools import find_packages, setup

setup(
    name="sagemaker-hyperpod-usage-report",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "boto3>=1.26.0",
        "pandas>=1.5.0",
        "awswrangler>=3.0.0",
        "fpdf>=1.7.2",
    ],
    python_requires=">=3.8",
)
