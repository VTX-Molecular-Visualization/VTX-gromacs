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
        generated_headers_path = os.path.join(self.folders.build , "api", "legacy", "include") # TODO : test usefullness ?
        self.cpp.source.includedirs = [
            os.path.join(self.recipe_folder, "src")
            , os.path.join(self.recipe_folder, "api", "legacy", "include")
            , generated_headers_path # doesn't work :'(
        ]  
        self.cpp.source.components["gmx"].includedirs         = self.cpp.source.includedirs
        self.cpp.source.components["gromacs"].includedirs     = self.cpp.source.includedirs
        self.cpp.source.components["muparser"].includedirs    = self.cpp.source.includedirs
        bt = "." if self.settings.os != "Windows" else str(self.settings.build_type)
        self.cpp.build.components["gmx"].libdirs = [bt]
        self.cpp.build.components["gromacs"].libdirs = [bt]
        self.cpp.build.components["muparser"].libdirs = [bt]
        
        
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
        
        bt = "." if self.settings.os != "Windows" else str(self.settings.build_type)
        self.cpp_info.components["gmx"].libdirs = [bt]
        self.cpp_info.components["gromacs"].libdirs = [bt]
        self.cpp_info.components["muparser"].libdirs = [bt]
        
        self.cpp_info.components["muparser"].libs = ["muparser"]
        self.cpp_info.components["bye"].set_property("cmake_target_name", "vtx-gromacs::muparser")
        
        self.cpp_info.components["gromacs"].libs = ["gromacs"]
        self.cpp_info.components["gromacs"].requires = ["muparser"]
        
        self.cpp_info.components["gmx"].libs = ["gmx"]
        self.cpp_info.components["gmx"].requires = ["gromacs"]
        
        
