#!/usr/bin/env bash
# Build the HARFANG 3.2.7 Python module from source on macOS and install it into a venv.
# PyPI only ships Windows wheels for harfang.
#
# Requires: Xcode command line tools, git, cmake, ninja, and a python3 >= 3.8.
#
# Usage: tools/build_harfang_macos.sh [WORK_DIR] [VENV_DIR]
#   WORK_DIR  where harfang3d is cloned and built (default: ./harfang-build)
#   VENV_DIR  the venv to create or reuse          (default: ./venv)
set -euo pipefail

HG_TAG=v3.2.7
PYTHON=${PYTHON:-python3}
WORK_DIR=$(mkdir -p "${1:-harfang-build}" && cd "${1:-harfang-build}" && pwd)
VENV_DIR=${2:-venv}

[ -x "$VENV_DIR/bin/python" ] || "$PYTHON" -m venv "$VENV_DIR"
VENV_DIR=$(cd "$VENV_DIR" && pwd)
VENV_PY="$VENV_DIR/bin/python"
# pypeg2 is needed by the FABGen binding generator, tqdm by the sandbox
"$VENV_PY" -m pip install --quiet pypeg2 tqdm

SRC="$WORK_DIR/harfang3d"
if [ ! -d "$SRC" ]; then
	git clone --branch "$HG_TAG" --depth 1 --recurse-submodules --shallow-submodules \
		https://github.com/harfang3d/harfang3d.git "$SRC"
	git clone --depth 1 https://github.com/ejulien/FABGen.git "$SRC/extern/fabgen"
	# macOS fixes, upstream as harfang3d/harfang3d#59: arm64 must not force an embedded build, the CPython
	# module must not link libpython, and GLFW must not change the working directory.
	git -C "$SRC" apply <<'EOF'
diff --git a/CMakeLists.txt b/CMakeLists.txt
--- a/CMakeLists.txt
+++ b/CMakeLists.txt
@@ -74,8 +74,8 @@ if(NOT CMAKE_CONFIGURATION_TYPES AND NOT CMAKE_BUILD_TYPE)
 	SET(CMAKE_BUILD_TYPE RelWithDebInfo)
 endif()
 
-if(${CMAKE_SYSTEM_PROCESSOR} MATCHES "arm") 
-	message(STATUS "! Forcing embedded build since system processor is 'arm'")
+if(CMAKE_SYSTEM_PROCESSOR MATCHES "^arm" AND NOT CMAKE_SYSTEM_PROCESSOR MATCHES "^arm64")
+	message(STATUS "! Forcing embedded build since system processor is 32-bit 'arm'")
 	set(HG_EMBEDDED ON FORCE)
 endif()
 
diff --git a/harfang/platform/glfw/window_system.cpp b/harfang/platform/glfw/window_system.cpp
--- a/harfang/platform/glfw/window_system.cpp
+++ b/harfang/platform/glfw/window_system.cpp
@@ -63,6 +63,11 @@ static bool glfw_initialized = false;
 
 void WindowSystemInit() {
 	glfwSetErrorCallback(ErrorCallback);
+#if __APPLE__
+	// Keep the working directory. By default GLFW changes it to the Resources folder of the app bundle the
+	// process runs from, e.g. Python.app of a framework CPython, which breaks every relative asset path.
+	glfwInitHint(GLFW_COCOA_CHDIR_RESOURCES, GLFW_FALSE);
+#endif
 	int ret = glfwInit();
 	__RASSERT_MSG__(ret == GLFW_TRUE, "Failed to initialize window system");
 	ConnectWindowSystemSignals();
diff --git a/languages/hg_python/CMakeLists.txt b/languages/hg_python/CMakeLists.txt
--- a/languages/hg_python/CMakeLists.txt
+++ b/languages/hg_python/CMakeLists.txt
@@ -36,7 +36,12 @@ endif()
 
 target_compile_definitions(hg_python PUBLIC Py_LIMITED_API=0x03020000)
 target_include_directories(hg_python PUBLIC ${Python3_INCLUDE_DIRS})
-target_link_libraries(hg_python script engine foundation platform ${Python3_LIBRARIES})
+if(APPLE)
+	target_link_libraries(hg_python script engine foundation platform)
+	target_link_options(hg_python PRIVATE -undefined dynamic_lookup)
+else()
+	target_link_libraries(hg_python script engine foundation platform ${Python3_LIBRARIES})
+endif()
 set_target_properties(hg_python PROPERTIES FOLDER "harfang/languages")
 
 if(HG_PYTHON_PIP)
EOF
fi

cmake -S "$SRC" -B "$SRC/build" -G Ninja \
	-DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
	-DCMAKE_INSTALL_PREFIX="$SRC/install" \
	-DPython3_EXECUTABLE="$VENV_PY" \
	-DHG_FABGEN_PATH="$SRC/extern/fabgen" \
	-DHG_COMMIT_ID="$HG_TAG" \
	-DHG_BUILD_HG_PYTHON=ON -DHG_PYTHON_PIP=ON -DHG_BUILD_ASSETC=ON -DHG_REBUILD_GLFW=ON \
	-DHG_BUILD_ASSIMP_CONVERTER=OFF -DHG_BUILD_FBX_CONVERTER=OFF \
	-DHG_BUILD_GLTF_IMPORTER=OFF -DHG_BUILD_GLTF_EXPORTER=OFF \
	-DHG_BUILD_HG_LUA=OFF -DHG_BUILD_HG_GO=OFF -DHG_BUILD_CPP_SDK=OFF -DHG_BUILD_TESTS=OFF -DHG_BUILD_DOCS=OFF \
	-DHG_ENABLE_OPENVR_API=OFF -DHG_ENABLE_RECAST_DETOUR_API=OFF
ninja -C "$SRC/build" install

# Lay the module out like the pip package: harfang/{harfang.so, bin/assetc/...}, so that
# `import harfang` and `harfang.bin.assetc(...)` work as they do on Windows and Linux.
SITE=$("$VENV_PY" -c 'import sysconfig; print(sysconfig.get_paths()["platlib"])')
PKG="$SITE/harfang"
rm -rf "$PKG"
mkdir -p "$PKG/bin"
cp "$SRC/install/harfang.so" "$SRC"/install/*.dylib "$PKG/"
cp -R "$SRC/install/assetc" "$PKG/bin/"
echo 'from .harfang import *' > "$PKG/__init__.py"
cat > "$PKG/bin/__init__.py" <<'EOF'
import subprocess
from pathlib import Path


def __getattr__(name: str):
	binary = Path(__file__).parent / name / name
	if not binary.is_file():
		raise AttributeError(f"Unknown harfang tool {name}")

	def run(*args):
		return subprocess.run([str(binary), *args])

	return run
EOF

(cd /tmp && "$VENV_PY" -c 'import harfang, harfang.bin; harfang.bin.assetc')
echo "HARFANG installed into $VENV_DIR"
