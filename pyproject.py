[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "pixeltools"
version = "0.1.0"
description = "AOV and pixel analysis toolkit for simulation images"
authors = [
    { name="Sergio Gonzalez", email="you@example.com" }
]
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.8"
dependencies = [
    "PyQt5",
    "numpy",
    "opencv-python",
    "imageio",
    "OpenEXR"
]

[project.scripts]
pixeltools = "main:main"

[tool.setuptools.packages.find]
where = ["."]
