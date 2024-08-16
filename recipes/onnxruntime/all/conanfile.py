from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import fix_apple_shared_install_name, is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir, save
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version
import os
import sys
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
        "with_xnnpack": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_xnnpack": False,
    }

    @property
    def _protobuf_version(self):
        return "3.21.12"

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        self.options["boost"].header_only = True
        self.options["onnx"].disable_static_registration = True

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def requirements(self):
        self.requires("abseil/20240116.1", transitive_headers=True, transitive_libs=True)
        self.requires("boost/1.82.0", transitive_headers=True)
        self.requires("date/3.0.1", transitive_headers=True)
        self.requires("flatbuffers/23.5.26", transitive_headers=True, transitive_libs=True)
        self.requires("onnx/1.16.0", transitive_headers=True, transitive_libs=True)
        self.requires("protobuf/3.21.12", transitive_headers=True, transitive_libs=True)
        self.requires("ms-gsl/4.0.0", transitive_headers=True)
        self.requires("safeint/3.0.28", transitive_headers=True)
        for req in self.conan_data.get("requires", {}).get(self.version, []):
            self.requires(req)
        if self.settings.os != "Windows":
            self.requires(f"nsync/1.26.0", transitive_headers=True, transitive_libs=True)

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
        tc.variables["onnxruntime_USE_FULL_PROTOBUF"] = not self.dependencies["protobuf"].options.lite
        tc.variables["onnxruntime_BUILD_SHARED_LIB"] = self.options.shared
        tc.variables["onnxruntime_USE_XNNPACK"] = self.options.with_xnnpack

        tc.variables["onnxruntime_BUILD_UNIT_TESTS"] = False
        tc.variables["onnxruntime_USE_FLASH_ATTENTION"] = False
        tc.variables["onnxruntime_RUN_ONNX_TESTS"] = False
        tc.variables["onnxruntime_GENERATE_TEST_REPORTS"] = False
        tc.variables["onnxruntime_USE_MIMALLOC"] = False
        tc.variables["onnxruntime_ENABLE_PYTHON"] = False
        tc.variables["onnxruntime_BUILD_CSHARP"] = False
        tc.variables["onnxruntime_BUILD_JAVA"] = False
        tc.variables["onnxruntime_BUILD_NODEJS"] = False
        tc.variables["onnxruntime_BUILD_OBJC"] = False
        tc.variables["onnxruntime_BUILD_APPLE_FRAMEWORK"] = False
        tc.variables["onnxruntime_USE_DNNL"] = False
        tc.variables["onnxruntime_USE_NNAPI_BUILTIN"] = False
        tc.variables["onnxruntime_USE_RKNPU"] = False
        tc.variables["onnxruntime_USE_LLVM"] = False
        tc.variables["onnxruntime_ENABLE_MICROSOFT_INTERNAL"] = False
        tc.variables["onnxruntime_USE_VITISAI"] = False
        tc.variables["onnxruntime_USE_TENSORRT"] = False
        tc.variables["onnxruntime_SKIP_AND_PERFORM_FILTERED_TENSORRT_TESTS"] = True
        tc.variables["onnxruntime_USE_TENSORRT_BUILTIN_PARSER"] = False
        tc.variables["onnxruntime_TENSORRT_PLACEHOLDER_BUILDER"] = False
        tc.variables["onnxruntime_USE_TVM"] = False
        tc.variables["onnxruntime_TVM_CUDA_RUNTIME"] = False
        tc.variables["onnxruntime_TVM_USE_HASH"] = False
        tc.variables["onnxruntime_CROSS_COMPILING"] = False
        tc.variables["onnxruntime_DISABLE_CONTRIB_OPS"] = False
        tc.variables["onnxruntime_DISABLE_ML_OPS"] = False
        tc.variables["onnxruntime_DISABLE_RTTI"] = False
        tc.variables["onnxruntime_DISABLE_EXCEPTIONS"] = False
        tc.variables["onnxruntime_MINIMAL_BUILD"] = False
        tc.variables["onnxruntime_EXTENDED_MINIMAL_BUILD"] = False
        tc.variables["onnxruntime_MINIMAL_BUILD_CUSTOM_OPS"] = False
        tc.variables["onnxruntime_REDUCED_OPS_BUILD"] = False
        tc.variables["onnxruntime_ENABLE_LANGUAGE_INTEROP_OPS"] = False
        tc.variables["onnxruntime_USE_DML"] = False
        tc.variables["onnxruntime_USE_WINML"] = False
        tc.variables["onnxruntime_BUILD_MS_EXPERIMENTAL_OPS"] = False
        tc.variables["onnxruntime_USE_TELEMETRY"] = False
        tc.variables["onnxruntime_ENABLE_LTO"] = False
        tc.variables["onnxruntime_USE_ACL"] = False
        tc.variables["onnxruntime_USE_ACL_1902"] = False
        tc.variables["onnxruntime_USE_ACL_1905"] = False
        tc.variables["onnxruntime_USE_ACL_1908"] = False
        tc.variables["onnxruntime_USE_ACL_2002"] = False
        tc.variables["onnxruntime_USE_ARMNN"] = False
        tc.variables["onnxruntime_ARMNN_RELU_USE_CPU"] = False
        tc.variables["onnxruntime_ARMNN_BN_USE_CPU"] = False
        tc.variables["onnxruntime_ENABLE_NVTX_PROFILE"] = False
        tc.variables["onnxruntime_ENABLE_TRAINING"] = False
        tc.variables["onnxruntime_ENABLE_TRAINING_OPS"] = False
        tc.variables["onnxruntime_ENABLE_TRAINING_APIS"] = False
        tc.variables["onnxruntime_ENABLE_CPU_FP16_OPS"] = False
        tc.variables["onnxruntime_USE_NCCL"] = False
        tc.variables["onnxruntime_BUILD_BENCHMARKS"] = False
        tc.variables["onnxruntime_USE_ROCM"] = False
        tc.variables["onnxruntime_GCOV_COVERAGE"] = False
        tc.variables["onnxruntime_USE_MPI"] = False
        tc.variables["onnxruntime_ENABLE_MEMORY_PROFILE"] = False
        tc.variables["onnxruntime_ENABLE_CUDA_LINE_NUMBER_INFO"] = False
        tc.variables["onnxruntime_BUILD_WEBASSEMBLY"] = False
        tc.variables["onnxruntime_BUILD_WEBASSEMBLY_STATIC_LIB"] = False
        tc.variables["onnxruntime_ENABLE_WEBASSEMBLY_EXCEPTION_CATCHING"] = False
        tc.variables["onnxruntime_ENABLE_WEBASSEMBLY_API_EXCEPTION_CATCHING"] = False
        tc.variables["onnxruntime_ENABLE_WEBASSEMBLY_EXCEPTION_THROWING"] = False
        tc.variables["onnxruntime_ENABLE_WEBASSEMBLY_THREADS"] = False
        tc.variables["onnxruntime_ENABLE_WEBASSEMBLY_DEBUG_INFO"] = False
        tc.variables["onnxruntime_ENABLE_WEBASSEMBLY_PROFILING"] = False
        tc.variables["onnxruntime_ENABLE_EAGER_MODE"] = False
        tc.variables["onnxruntime_ENABLE_LAZY_TENSOR"] = False
        tc.variables["onnxruntime_ENABLE_EXTERNAL_CUSTOM_OP_SCHEMAS"] = False
        tc.variables["onnxruntime_ENABLE_CUDA_PROFILING"] = False
        tc.variables["onnxruntime_ENABLE_ROCM_PROFILING"] = False
        tc.variables["onnxruntime_USE_CANN"] = False
        tc.generate()
        deps = CMakeDeps(self)
        deps.generate()
        env = VirtualBuildEnv(self)
        env.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure(build_script_folder="cmake", cli_args=["--compile-no-warning-as-error"])
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        fix_apple_shared_install_name(self)

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
                "libs": ["onnxruntime_flatbuffers"],
                "requires": ["flatbuffers::flatbuffers"]
            },
            "onnxruntime_common": {
                "target": "onnxruntime_common",
                "libs": ["onnxruntime_common"],
                "requires": ["protobuf::libprotobuf", "onnx::onnx", "abseil::abseil", "cpuinfo::cpuinfo", "ms-gsl::ms-gsl", "boost::headers", "safeint::safeint", "date::date"]
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
