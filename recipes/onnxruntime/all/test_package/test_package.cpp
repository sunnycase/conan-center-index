#include <onnxruntime/core/session/onnxruntime_cxx_api.h>
#include <onnxruntime/core/framework/execution_provider.h>
#include <onnxruntime/core/providers/cpu/cpu_provider_factory_creator.h>

using namespace onnxruntime;

std::unique_ptr<IExecutionProvider> DefaultCpuExecutionProvider(bool enable_arena) {
    return CPUProviderFactoryCreator::Create(enable_arena)->CreateProvider();
}

int main() {
    Ort::Value value(nullptr);
    DefaultCpuExecutionProvider(true);
    return 0;
}
