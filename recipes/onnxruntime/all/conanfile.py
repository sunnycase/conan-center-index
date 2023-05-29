from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, get, rmdir, save
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version
import os
import textwrap

required_conan_version = ">=1.50.2 <1.51.0 || >=1.51.2"


class OnnxRuntimeConan(ConanFile):
    name = "onnxruntime"
    description = "Open standard for machine learning interoperability."
    license = "Apache-2.0"
    topics = ("machine-learning", "deep-learning", "neural-network")
    homepage = "https://github.com/onnx/onnx"
    url = "https://github.com/conan-io/conan-center-index"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    @property
    def _protobuf_version(self):
        # onnx < 1.9.0 doesn't support protobuf >= 3.18
        return "3.21.4" if Version(self.version) >= "1.9.0" else "3.17.1"

    def export_sources(self):
        for p in self.conan_data.get("patches", {}).get(self.version, []):
            copy(self, p["patch_file"], self.recipe_folder, self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        self.options["boost"].header_only = True
        self.options["onnx"].disable_static_registration = True

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def requirements(self):
        self.requires(f"protobuf/{self._protobuf_version}")
        for req in self.conan_data.get("requires", {}).get(self.version, []):
            self.requires(req)
        if self.settings.os != "Windows":
            self.requires(f"nsync/1.25.0")

    def validate(self):
        if self.info.settings.compiler.cppstd:
            check_min_cppstd(self, 17)

    def build_requirements(self):
        if hasattr(self, "settings_build"):
            self.tool_requires(f"protobuf/{self._protobuf_version}")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["onnxruntime_BUILD_UNIT_TESTS"] = False
        tc.variables["onnxruntime_USE_FLASH_ATTENTION"] = False
        tc.variables["onnxruntime_BUILD_SHARED_LIB"] = self.options.shared
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()
        env = VirtualBuildEnv(self)
        env.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure(build_script_folder="cmake")
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

        # TODO: to remove in conan v2 once legacy generators removed
        self._create_cmake_module_alias_targets(
            os.path.join(self.package_folder, self._module_file_rel_path),
            {component["target"]:f"onnxruntime::{component['target']}" for component in self._onnx_components.values()}
        )

    def _create_cmake_module_alias_targets(self, module_file, targets):
        content = ""
        for alias, aliased in targets.items():
            content += textwrap.dedent(f"""\
                if(TARGET {aliased} AND NOT TARGET {alias})
                    add_library({alias} INTERFACE IMPORTED)
                    set_property(TARGET {alias} PROPERTY INTERFACE_LINK_LIBRARIES {aliased})
                endif()
            """)
        save(self, module_file, content)

    @property
    def _module_file_rel_path(self):
        return os.path.join("lib", "cmake", f"conan-official-{self.name}-targets.cmake")

    @property
    def _onnx_components(self):
        components = {
            "onnxruntime_flatbuffers": {
                "target": "onnxruntime_flatbuffers",
                "libs": ["onnxruntime_flatbuffers"]
            },
            "onnxruntime_common": {
                "target": "onnxruntime_common",
                "libs": ["onnxruntime_common"],
                "requires": ["protobuf::libprotobuf", "onnx::onnx", "abseil::abseil", "cpuinfo::cpuinfo", "ms-gsl::_ms-gsl", "boost::boost", "safeint::safeint"]
            },
            "onnxruntime_mlas": {
                "target": "onnxruntime_mlas",
                "libs": ["onnxruntime_mlas"]
            },
            "onnxruntime_graph": {
                "target": "onnxruntime_graph",
                "libs": ["onnxruntime_graph"],
                "requires": ["onnxruntime_flatbuffers"]
            },
            "onnxruntime_framework": {
                "target": "onnxruntime_framework",
                "libs": ["onnxruntime_framework"],
                "requires": ["onnxruntime_common", "onnxruntime_mlas"]
            },
            "onnxruntime_util": {
                "target": "onnxruntime_util",
                "libs": ["onnxruntime_util"],
                "requires": ["onnxruntime_mlas"]
            },
            "onnxruntime_optimizer": {
                "target": "onnxruntime_optimizer",
                "libs": ["onnxruntime_optimizer"],
                "requires": ["onnxruntime_graph"]
            },
            "onnxruntime_session": {
                "target": "onnxruntime_session",
                "libs": ["onnxruntime_session"],
                "requires": ["onnxruntime_providers", "onnxruntime_graph", "onnxruntime_optimizer"]
            },
            "onnxruntime_providers": {
                "target": "onnxruntime_providers",
                "libs": ["onnxruntime_providers"],
                "requires": ["re2::re2", "onnxruntime_framework", "onnxruntime_util"]
            }
        }
        return components

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "onnxruntime")

        def _register_components(components):
            for comp_name, comp_values in components.items():
                target = comp_values["target"]
                libs = comp_values.get("libs", [])
                defines = comp_values.get("defines", [])
                requires = comp_values.get("requires", [])
                self.cpp_info.components[comp_name].set_property("cmake_target_name", target)
                self.cpp_info.components[comp_name].libs = libs
                self.cpp_info.components[comp_name].defines = defines
                self.cpp_info.components[comp_name].requires = requires

                # TODO: to remove in conan v2 once cmake_find_package_* generators removed
                self.cpp_info.components[comp_name].names["cmake_find_package"] = target
                self.cpp_info.components[comp_name].names["cmake_find_package_multi"] = target
                self.cpp_info.components[comp_name].build_modules["cmake_find_package"] = [self._module_file_rel_path]
                self.cpp_info.components[comp_name].build_modules["cmake_find_package_multi"] = [self._module_file_rel_path]
                if self.settings.os != "Windows":
                    self.cpp_info.components[comp_name].system_libs = ["dl"]
                    self.cpp_info.components[comp_name].requires += ["nsync::nsync_cpp"]
                if str(self.settings.arch).startswith("riscv"):
                    self.cpp_info.components[comp_name].system_libs += ["atomic"]

        _register_components(self._onnx_components)

        if is_apple_os(self):
            self.cpp_info.components["onnxruntime_common"].frameworks = ['Foundation']

        # TODO: to remove in conan v2 once legacy generators removed
        self.cpp_info.names["cmake_find_package"] = "onnxruntime"
        self.cpp_info.names["cmake_find_package_multi"] = "onnxruntime"
