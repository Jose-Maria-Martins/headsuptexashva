#!/usr/bin/env python3
"""
Simple build script that compiles C++ without CMake.
This bypasses all the CMake/pybind11 detection issues.
"""

import os
import subprocess
import sys
import sysconfig
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running: {cmd}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        print(f"STDOUT: {result.stdout}")
        return True
    except Exception as e:
        print(f"Exception running {cmd}: {e}")
        return False

def main():
    print("[BUILD] Simple C++ Build Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("cpp_engine").exists():
        print("[ERROR] Run this from the project root directory")
        return False
    
    # Check if venv is activated
    if not os.environ.get('VIRTUAL_ENV'):
        print("[WARN] Virtual environment not activated")
        print("Run: call venv\\Scripts\\activate.bat")
        return False
    
    print("[OK] Virtual environment detected")
    
    # Get Python executable
    python_exe = sys.executable
    print(f"[OK] Using Python: {python_exe}")
    
    # Get pybind11 include directory
    try:
        import pybind11
        
        pybind11_include = pybind11.get_include()
        python_include = sysconfig.get_path('include')
        
        print(f"[OK] Found pybind11 include: {pybind11_include}")
        print(f"[OK] Found Python include: {python_include}")
    except ImportError:
        print("[ERROR] pybind11 not found. Run: pip install pybind11")
        return False
    
    # Create build directory
    build_dir = Path("build_simple")
    if build_dir.exists():
        import shutil
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    print(f"[OK] Created build directory: {build_dir}")
    
    # Compile command - use absolute paths since we're in build_simple subdir
    project_root = Path.cwd()
    sources = [
        str(project_root / "cpp_engine/src/poker_engine.cpp"),
        str(project_root / "cpp_engine/src/hand_evaluator.cpp"), 
        str(project_root / "cpp_engine/src/simulator.cpp"),
        str(project_root / "cpp_engine/src/bindings.cpp")
    ]
    
    include_dirs = [
        str(project_root / "cpp_engine/include"),
        pybind11_include,
        python_include
    ]
    
    # Try to find a C++ compiler
    compilers = ["cl.exe", "g++.exe", "gcc.exe"]
    compiler = None
    
    for comp in compilers:
        result = subprocess.run(f"where {comp}", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            compiler = comp
            print(f"[OK] Found compiler: {compiler}")
            break
    
    if not compiler:
        print("[ERROR] No C++ compiler found!")
        print("Please install one of:")
        print("  1. Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/")
        print("  2. MinGW-w64: https://github.com/msys2/msys2-installer/releases")
        return False
    
    # Build the compile command based on compiler
    if compiler == "cl.exe":
        # MSVC - quote paths with spaces
        include_flags = []
        for inc_dir in include_dirs:
            include_flags.append(f'/I"{inc_dir}"')
        
        # Quote source files too
        quoted_sources = [f'"{src}"' for src in sources]
        
        # Get Python library path
        python_lib = sysconfig.get_config_var('LIBDIR')
        python_version = f"{sys.version_info.major}{sys.version_info.minor}"
        python_lib_file = f"python{python_version}.lib"
        
        # Correct order: cl.exe [options] [sources] /link [linker options]
        cmd_parts = [
            "cl.exe",
            "/std:c++17",
            "/O2",
            "/LD",
            "/EHsc",
            " ".join(include_flags),
            " ".join(quoted_sources),
            f'/link /OUT:poker_engine.pyd /LIBPATH:"{python_lib}"',
            python_lib_file
        ]
    else:
        # GCC/MinGW
        cmd_parts = [
            compiler,
            "-std=c++17",
            "-O3",
            "-shared",
            "-fPIC",
            "-I" + " -I".join(include_dirs),
            "-o", "poker_engine.pyd",
            " ".join(sources)
        ]
    
    compile_cmd = " ".join(cmd_parts)
    print(f"[BUILD] Compiling with: {compile_cmd}")
    
    # Try to compile
    if run_command(compile_cmd, cwd=build_dir):
        print("[OK] Compilation successful!")
        
        # Copy to poker_ai directory
        import shutil
        pyd_file = build_dir / "poker_engine.pyd"
        if pyd_file.exists():
            shutil.copy2(pyd_file, "poker_ai/")
            print("[OK] Copied poker_engine.pyd to poker_ai/")
            
            # Test import
            print("[TEST] Testing import...")
            try:
                import poker_ai.poker_engine
                print("[SUCCESS] C++ engine is working!")
                return True
            except ImportError as e:
                print(f"[ERROR] Import failed: {e}")
                return False
        else:
            print("[ERROR] poker_engine.pyd not found after compilation")
            return False
    else:
        print("[ERROR] Compilation failed")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n[SUCCESS] Build completed successfully!")
        print("Run: python verify_install.py")
    else:
        print("\n[FALLBACK] Use Python-only mode")
        print("Run: python experiments/run_experiment.py")
