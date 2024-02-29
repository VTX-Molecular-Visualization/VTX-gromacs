import os
from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.scm import Git
from conan.tools.files import copy
from pathlib import Path

class VtxGromacsRecipe(ConanFile):
    name = "gromacs"
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
    
    exports_sources = "CMakeLists.txt", "src/*", "cmake/*", "share/*", "tests/*", "api/*", "COPYING", "AUTHORS", "CITATION.cff", "docs/*", "scripts/*", "admin/*"
        
    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self)  
        
        # Add generated include dir for editable mode.
        generated_headers_path = os.path.join(self.folders.build , "api", "legacy", "include") # TODO : test usefullness ?
        self.cpp.source.includedirs = [
            os.path.join(self.recipe_folder, "src")
            , os.path.join(self.recipe_folder, "api", "legacy", "include")
            , generated_headers_path 
        ]  
        
        self.cpp.build.components["gmx"     ].libdirs = self.cpp.build.libdirs
        self.cpp.build.components["gromacs" ].libdirs = self.cpp.build.libdirs
        self.cpp.build.components["muparser"].libdirs = self.cpp.build.libdirs
        
        self.cpp.source.components["gmx"     ].includedirs = self.cpp.source.includedirs
        self.cpp.source.components["gromacs" ].includedirs = self.cpp.source.includedirs
        self.cpp.source.components["muparser"].includedirs = self.cpp.source.includedirs
        
    def _generated_cmake_prefix(self):
        return "gmxbin-"
    
    def build_requirements(self):
        self.tool_requires("cmake/3.27.0")
        
    def build(self):
        cmake = CMake(self)
        cmake.configure(cli_args=[
            "-DGMX_FFT_LIBRARY=fftpack"
            , "-DBUILD_SHARED_LIBS=off"
            , "-DGMX_PREFER_STATIC_LIBS=on"
            , "-DGMX_BUILD_SHARED_EXE=OFF"
        ]) # build with slow fft algorithm. Since we won't use mdrun, it doesn't really matter
        cmake.build()
        
        # Copies the bin files necessary to compile against gromacs into the root build dir
        #  We need to do that as the lib subdir doesn't seems to be found from outside the package
        dest_libdir = os.path.join(self.build_folder, os.path.join(self.build_folder, self.cpp.build.libdirs[0]))
        cmake_dir = os.path.join(self.recipe_folder, "cmake")
        if not Path(cmake_dir).exists():
            Path(cmake_dir).mkdir()
        cmake_dir = os.path.join(cmake_dir, "out")
        if not Path(cmake_dir).exists():
            Path(cmake_dir).mkdir()
        
        cmake_file_name = f"{self._generated_cmake_prefix()}{self.settings.build_type}.cmake"
        cmake_file_path = os.path.join(cmake_dir, cmake_file_name)
        cmake_file_content = """vtx_register_build_directory_copy("%s" "external/tools/mdprep/gromacs")""" % ((Path(dest_libdir) / "bin").as_posix())
        Path(cmake_file_path).write_text(cmake_file_content)
        try : # copy function throws when it tries to copy a file that is already there. 
            copy(self, pattern="*.a"       , src=self.build_folder, dst=dest_libdir, keep_path=False)
            copy(self, pattern="*.so"      , src=self.build_folder, dst=dest_libdir, keep_path=False)
            copy(self, pattern="*.lib"     , src=self.build_folder, dst=dest_libdir, keep_path=False)
            copy(self, pattern="*.dylib"   , src=self.build_folder, dst=dest_libdir, keep_path=False)
            copy(self, pattern="*.dll"     , src=self.build_folder, dst=dest_libdir, keep_path=False)
            copy(self, pattern="*.exe"     , src=self.build_folder, dst=dest_libdir, keep_path=False)
            
        except :
            None
    
    def package(self):
        cmake = CMake(self)
        cmake.install()
        copy(self, pattern=os.path.join("bin","*.dll"), src=self.build_folder, dst=os.path.join(self.package_folder, "external", "tools", "mdprep", "gromacs"))

    def package_info(self):
        self.cpp_info.includedirs = ['include', os.path.join('api', 'legacy', 'include') ]
        
        self.cpp_info.components["muparser"].libs = ["muparser"]
        self.cpp_info.components["muparser"].set_property("cmake_targetName", "vtx-gromacs::muparser")
        
        self.cpp_info.components["gromacs"].libs = ["gromacs"]
        self.cpp_info.components["gromacs"].requires = ["muparser"]
        self.cpp_info.components["gromacs"].set_property("cmake_targetName", "vtx-gromacs::gromacs")
        
        # Give away cmake code to be executed by the consumer of this package
        generated_cmake = "cmake/out/%s%s.cmake" % (self._generated_cmake_prefix(), self.settings.build_type)
        self.cpp_info.set_property("cmake_build_modules", [generated_cmake])
        
        
