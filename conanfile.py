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
        """
        # self.folders.source = "."
        # self.folders.build = os.path.join("build", str(self.settings.build_type))
        # self.folders.generators = os.path.join(self.folders.build, "generators")
        
        # self.cpp.package.libs = ["gromacs", "gmx", "muparser"]
        self.cpp.package.includedirs = [*self.cpp.package.includedirs, ".", os.path.join(self.folders.build, 'api', 'legacy', 'include'), os.path.join('api', 'legacy', 'include'), os.path.join(self.recipe_folder, "src"), os.path.join('src', 'include')]
        self.cpp.source.includedirs = [*self.cpp.source.includedirs, *self.cpp.package.includedirs]
        
        # self.cpp.package.libdirs = ["lib"]  
        
        # self.cpp.build.libdirs = ["."]
        return 
        """
        
        # Add generated include dir for editable mode.
        generated_headers_path = os.path.join(self.folders.build , "api", "legacy", "include")
        #Path("D:/log.log").write_text("generated_headers_path : <{}>".format(str(generated_headers_path)))
        self.cpp.source.includedirs = [
            os.path.join(self.recipe_folder, "src")
            , os.path.join(self.recipe_folder, "api", "legacy", "include")
            , generated_headers_path # doesn't work :'(
        ]  
        
    def build(self):
        cmake = CMake(self)
        cmake.configure(cli_args=["-DGMX_FFT_LIBRARY=fftpack"]) # build with slow fft algorithm. Since we won't use mdrun, it doesn't really matter
        cmake.build()
        
        # Copies the bin files necessary to compile against gromacs into the root build dir
        #  We need to do that as the lib subdir doesn't seems to be found from outside the package
        dest_libdir = os.path.join(self.build_folder, os.path.join(self.build_folder, self.cpp.build.libdirs[0]))
        try : # copy function throws when it tries to copy a file that is already there. 
            copy(self, pattern="*.a"       , src=self.build_folder, dst=dest_libdir, keep_path=False)
            copy(self, pattern="*.so"      , src=self.build_folder, dst=dest_libdir, keep_path=False)
            copy(self, pattern="*.lib"     , src=self.build_folder, dst=dest_libdir, keep_path=False)
            copy(self, pattern="*.dylib"   , src=self.build_folder, dst=dest_libdir, keep_path=False)
            copy(self, pattern="*.dll"     , src=self.build_folder, dst=dest_libdir, keep_path=False)
        except :
            None
    
    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.includedirs = ['include', os.path.join('api', 'legacy', 'include') ] 
        self.cpp_info.libs = ["gromacs", "gmx", "muparser"]

