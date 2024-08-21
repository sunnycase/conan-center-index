import os
from conan import ConanFile
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.errors import ConanInvalidConfiguration


class NetHostConan(ConanFile):
    name = "nethost"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/dotnet/runtime"
    license = "MIT"
    description = "Provides the .NET app bootstrapper intended for use in the application directory."
    topics = (
        "conan",
        "nethost",
        "dotnet",
        "coreclr",
        "host"
    )
    settings = "os", "arch"
    options = {
        "shared": [True, False]
    }
    default_options = {
        "shared": False
    }

    def _nupkg_url(self):
        if self.settings.os == 'Windows':
            os = 'win'
        elif self.settings.os == 'Linux':
            os = 'linux'
        elif self.settings.os == 'Macos':
            os = 'osx'
        if self.settings.arch == 'x86':
            arch = 'x86'
        elif self.settings.arch == 'x86_64':
            arch = 'x64'
        elif self.settings.arch == 'armv8' or self.settings.arch == 'arm64':
            arch = 'arm64'
        if (not os) or (not arch):
            raise ConanInvalidConfiguration("Unsupported nethost os or arch")
        self.rid = '{}-{}'.format(os, arch)
        return 'https://www.nuget.org/api/v2/package/runtime.{}.Microsoft.NETCore.DotNetAppHost/{}'.format(self.rid, self.version)

    def build(self):
        get(self, self._nupkg_url())

    def package(self):
        src_dir = os.path.join('runtimes', self.rid, 'native')
        copy(self, '*.h', src=src_dir, dst=os.path.join(self.package_folder, "include"))
        if self.options.shared:
            copy(self, 'nethost.dll', src=src_dir, dst=os.path.join(self.package_folder, "bin"))
            copy(self, 'nethost.lib', src=src_dir, dst=os.path.join(self.package_folder, "lib"))
            copy(self, 'libnethost.so', src=src_dir, dst=os.path.join(self.package_folder, "lib"))
            copy(self, 'libnethost.dylib', src=src_dir, dst=os.path.join(self.package_folder, "lib"))
        else:
            copy(self, 'libnethost.lib', src=src_dir, dst=os.path.join(self.package_folder, "lib"))
            copy(self, 'libnethost.a', src=src_dir, dst=os.path.join(self.package_folder, "lib"))

    def package_info(self):
        if self.settings.os == 'Windows' and not self.options.shared:
            self.cpp_info.libs = ["libnethost"]
        else:
            self.cpp_info.libs = ["nethost"]
        if not self.options.shared:
            self.cpp_info.defines.append("NETHOST_USE_AS_STATIC")
