@echo off
echo ========================================
echo REBUILDING C++ ENGINE - INFINITE LOOP FIX
echo ========================================
echo.
echo Fixed: Betting round infinite loop bug
echo Added: Action counter + improved termination logic
echo.
echo Open "x64 Native Tools Command Prompt for VS"
echo Then run these commands:
echo.
echo cd "C:\Users\Host\Documents\hva\Heads-Up Poker"
echo call venv\Scripts\activate.bat
echo.
echo cl /O2 /EHsc /std:c++17 /I"venv\Lib\site-packages\pybind11\include" /I"%PYTHON_INCLUDE%" /Icpp_engine\include /LD cpp_engine\src\simulator.cpp cpp_engine\src\hand_evaluator.cpp cpp_engine\src\bindings.cpp /link /OUT:poker_ai\poker_engine.pyd "%PYTHON_LIB%"
echo.
echo ========================================
echo After rebuilding, test with:
echo python experiments\test_cpp_v2_bot.py --seeds 10 --matches 100 --hands 100
echo.
pause


