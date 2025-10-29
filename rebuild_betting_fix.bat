@echo off
echo ========================================
echo REBUILDING - RESTORED ORIGINAL BETTING LOOP
echo ========================================
echo.
echo Fixed: Removed premature breaks after CALL/CHECK
echo Restored: Original betting termination logic
echo.
pause
echo.
echo Opening Visual Studio Command Prompt...
echo Please run these commands:
echo.
echo cd "C:\Users\Host\Documents\hva\Heads-Up Poker"
echo call venv\Scripts\activate.bat
echo.
echo cl /O2 /EHsc /std:c++17 /I"venv\Lib\site-packages\pybind11\include" /I"C:\Users\Host\AppData\Local\Programs\Python\Python313\Include" /Icpp_engine\include /LD cpp_engine\src\simulator.cpp cpp_engine\src\hand_evaluator.cpp cpp_engine\src\bindings.cpp /link /OUT:poker_ai\poker_engine.pyd "C:\Users\Host\AppData\Local\Programs\Python\Python313\libs\python313.lib"
echo.
pause


