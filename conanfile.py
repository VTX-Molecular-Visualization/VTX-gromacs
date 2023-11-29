import os
from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.scm import Git
from conan.tools.files import copy

from pathlib import Path

class VtxGromacsRecipe(ConanFile):
    name = "vtx-gromacs"
    version = "2024.0"
    package_type = "library"
    
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False]
        , "fPIC": [True, False]
    }
    default_options = {
        "shared": False
        , "fPIC": True
    }
    
    generators = "CMakeDeps", "CMakeToolchain"
    
    exports_sources = "CMakeLists.txt", "src/*", "cmake/*"
        
    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def generate(self):
        # Conan seems to automatically add [recipe_folder]/include to the cmake generated include list for this package.
        # However, gromacs keeps its header files alongside its sources, so we need to create an include folder ourselves
        #   On a personal note, I don't like this design and maybe we could change it someway in the future
        # copy(self, "*.h", os.path.join(self.recipe_folder, "src"), os.path.join(self.recipe_folder, "include"))
        return

    def layout(self):
        cmake_layout(self)  
        # Add generated include dir for editable mode.
        self.cpp.source.includedirs = [
            os.path.join(self.recipe_folder, "api", "legacy", "include")
            , os.path.join(self.recipe_folder, "src")
        ]  
        
    def build(self):
        cmake = CMake(self)
        cmake.configure(cli_args=["-DGMX_FFT_LIBRARY=fftpack"])
        cmake.build()
        
        # Copies the bin files necessary to compile against gromacs into the root build dir
        #  We need to do that as the lib subdir doesn't seems to be found from outside the package
        dest_libdir = os.path.join(self.build_folder, os.path.join(self.build_folder, self.cpp.build.libdirs[0]))
        copy(self, pattern="*.a"       , src=self.build_folder, dst=dest_libdir, keep_path=False)
        copy(self, pattern="*.so"      , src=self.build_folder, dst=dest_libdir, keep_path=False)
        copy(self, pattern="*.lib"     , src=self.build_folder, dst=dest_libdir, keep_path=False)
        copy(self, pattern="*.dylib"   , src=self.build_folder, dst=dest_libdir, keep_path=False)
        copy(self, pattern="*.dll"     , src=self.build_folder, dst=dest_libdir, keep_path=False)
    
    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["gromacs"]

