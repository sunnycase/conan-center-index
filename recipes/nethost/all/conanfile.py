import os
from conans import CMake, ConanFile, tools
from conans.errors import ConanInvalidConfiguration
from conans.tools import Version


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
        elif self.settings.arch == 'armv8':
            arch = 'arm64'
        if (not os) or (not arch):
            raise ConanInvalidConfiguration("Unsupported nethost os or arch")
        self.rid = '{}-{}'.format(os, arch)
        return 'https://www.nuget.org/api/v2/package/runtime.{}.Microsoft.NETCore.DotNetAppHost/{}'.format(self.rid, self.version)

    def build(self):
        tools.get(self._nupkg_url())

    def package(self):
        src_dir = os.path.join('runtimes', self.rid, 'native')
        self.copy('*.h', src=src_dir, dst="include")
        if self.options.shared:
            self.copy('nethost.dll', src=src_dir, dst="bin")
            self.copy('nethost.lib', src=src_dir, dst="lib")
            self.copy('libnethost.so', src=src_dir, dst="lib")
            self.copy('libnethost.dylib', src=src_dir, dst="lib")
        else:
            self.copy('libnethost.lib', src=src_dir, dst="lib")
            self.copy('libnethost.a', src=src_dir, dst="lib")

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "nethost"
        self.cpp_info.names["cmake_find_package_multi"] = "nethost"
        if self.settings.os == 'Windows' and not self.options.shared:
            self.cpp_info.libs = ["libnethost"]
        else:
            self.cpp_info.libs = ["nethost"]
        if not self.options.shared:
            self.cpp_info.defines.append("NETHOST_USE_AS_STATIC")
