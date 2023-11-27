import os
from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.scm import Git
from conan.tools.files import copy

class VtxGromacsRecipe(ConanFile):
    name = "vtx-gromacs"
    version = "2024.0"
    package_type = "library"
    
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    
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
        None

    def layout(self):
        cmake_layout(self)  
        # Add generated include dir for editable mode.
        self.cpp.source.includedirs = ["include", os.path.join(self.recipe_folder, "api", "legacy", "include")]  
        
    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        None
        #self.cpp_info.libs = ["vtx-gromacs"]
        #self.cpp_info.names["generator_name"] = "Gromacs"
        #self.cpp_info.libs = ["gromacs"] # If link fail, we should investigate this line

