# TODO: Foreman Toolkit Campaign - Refactor config_tool.py for Modular C++ Generation

## Tasks
- [ ] Modify run_master_orchestrator to return modular code blocks dict instead of single string
- [ ] Implement assemble_platformio function: creates PlatformIO project structure (src/, include/), writes blocks to files, generates platformio.ini
- [ ] Implement assemble_monolith function: concatenates blocks into single .ino file
- [ ] Add --output-format CLI argument (choices: 'platformio', 'monolith'; default 'monolith')
- [ ] Update forge_firmware_task to use new assembly based on format
- [ ] Update conductor_server.py: add 'format' query param to /forge, update subprocess call, handle PlatformIO as zip file
- [ ] Test both output formats
- [ ] Update documentation if needed

## Information Gathered
- run_master_orchestrator assembles C++ code into sections and replaces placeholders in USER_CPP_TEMPLATE.
- Current output is monolithic .ino file.
- Need to provide both monolithic and PlatformIO multi-file outputs.
- CLI uses argparse, server calls config_tool.py via subprocess.

## Plan
- Modify run_master_orchestrator to build and return a dict like {'includes': str, 'globals': str, 'functions': str, 'setup': str, 'loop': str, 'ai_block': str}.
- assemble_platformio(blocks, output_dir): Create dirs, write main.cpp (includes + ai_block + globals + functions + setup + loop), config.h (globals?), platformio.ini.
- assemble_monolith(blocks): Use existing template logic to concatenate into .ino string.
- CLI: Add --output-format arg.
- forge_firmware_task: Based on format, call appropriate assembler.
- Server: Add format param, pass to subprocess, for platformio zip the output dir.

## Dependent Files
- config_tool.py
- conductor_server.py
