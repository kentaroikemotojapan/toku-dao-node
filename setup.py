from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "and_geometry_cpp",
        ["and_geometry_core.cpp"],
        cxx_std=17,
    ),
]

setup(
    name="and_geometry_cpp",
    version="1.0.0",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)