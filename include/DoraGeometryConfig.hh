#ifndef DORA_GEOMETRY_CONFIG_HH
#define DORA_GEOMETRY_CONFIG_HH
#include <cstdlib>
#include <cmath>
#include <stdexcept>
#include <string>
namespace DoraConfig {
// Millimetres. Plug depth is a legacy assumption, NOT a measured dimension.
inline double PositiveLength(const char* name, double fallback, double upper) {
    const char* value = std::getenv(name);
    if (!value) return fallback;
    char* end = nullptr;
    double result = std::strtod(value, &end);
    if (end == value || *end != '\0' || !std::isfinite(result) || result <= 0 || result >= upper)
        throw std::runtime_error(std::string(name) + ": expected a finite positive length below " + std::to_string(upper) + " mm");
    return result;
}
inline double SourceZmm() { return PositiveLength("DORA_SOURCE_Z_MM", 120.0, 800.0); }
inline double PlugInnerZmm() { return PositiveLength("DORA_PLUG_INNER_Z_MM", 120.0, 300.0); }
// Signed displacement from the irradiation centre, in millimetres.
inline double HolderXmm() {
    const char* value = std::getenv("DORA_HOLDER_X_MM");
    if (!value) return 0.0;

    char* end = nullptr;
    double result = std::strtod(value, &end);

    if (end == value || *end != '\0' || !std::isfinite(result)
        || std::abs(result) > 300.0) {
        throw std::runtime_error(
            "DORA_HOLDER_X_MM: expected a finite value "
            "between -300 and +300 mm"
        );
    }

    return result;
}
}
#endif
