from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.tools.scm import Version
import os

required_conan_version = ">=1.54.0"


class NcnnConan(ConanFile):
    name = "ncnn"
    description = "A C library for reading, creating, and modifying zip archives"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Tencent/ncnn"
    license = "BSD-3-Clause"
    topics = ("zip", "zip-archives", "zip-editing")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        pass

    def validate(self):
        pass

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=False)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["NCNN_BUILD_BENCHMARK"] = False
        tc.variables["NCNN_BUILD_TESTS"] = False
        tc.variables["NCNN_BUILD_TOOLS"] = False
        tc.variables["NCNN_BUILD_EXAMPLES"] = False
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "ncnn")
        self.cpp_info.set_property("cmake_target_name", "ncnn::ncnn")
        self.cpp_info.set_property("pkg_config_name", "ncnn")
        self.cpp_info.libs = ["ncnnd" if self.settings.build_type == "Debug" else "ncnn"]
