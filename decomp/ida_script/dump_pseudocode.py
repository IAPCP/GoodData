import os
import sys
import shutil
import typing
import logging
import traceback
import json

import ida_nalt
import idautils
import ida_hexrays
import ida_lines
import ida_loader
import idc
import ida_segment

force_decompile = False
RESULT_SUFFIX = ".decomp"

#? maybe we should clean the output file (log) each Analysis
logger = None

def skip_function(function_address) -> bool:
    """
    skip function if function not in .text section
    """
    segm = ida_segment.getseg(function_address)
    segm_name = ida_segment.get_segm_name(segm)
    if segm_name != ".text":    # TODO: may add other segments sooner
        logger.warning(f"Function {hex(function_address)} at segment {segm_name} is skipped")
        return True
    else:
        return False

def decompile_function(function_address: int) -> typing.Dict[str, typing.Any]:
    global logger
    function_info = {}
    function_info['name'] = idc.get_func_name(function_address)
    cfunc = ida_hexrays.decompile(function_address)
    pseudocode_obj = cfunc.get_pseudocode()
    pseudocode = ""
    for line_obj in pseudocode_obj:
        pseudocode += ida_lines.tag_remove(line_obj.line) + '\n'
    function_info['pseudocode'] = pseudocode
    function_info['address'] = function_address
    function_info['file_offset'] = ida_loader.get_fileregion_offset(function_address)
    return function_info

def decompile_binary() -> typing.List:
    global logger
    result = []
    for function_address in idautils.Functions():
        try:
            if skip_function(function_address):
                continue
            result.append(decompile_function(function_address))
        except Exception as e:
            logger.error(f"Decompile function failed, address: {hex(function_address)}, error: {e}")
    return result

def main():
    global logger
    
    # sys.arg[1] is dump path
    binary_name = ida_nalt.get_root_filename()
    
    # set logging format
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(binary_name)
    
    # Check binary decompile result
    result_file_name = binary_name + RESULT_SUFFIX
    result_file_path = os.path.join(idc.ARGV[1], result_file_name)
    if os.path.exists(result_file_path):
        if os.path.isfile(result_file_path):
            if force_decompile:
                os.unlink(result_file_path)           
                logger.info("Remove old decompile result")
            else:
                logger.info("Decompiled result file already exists, skip decompilation")
                return
        elif os.path.isdir(result_file_path):
            logger.error("Unexpected folder exists, remove it")
            shutil.rmtree(result_file_path)
        else:
            logger.error(f"Path error, {result_file_path}")
            raise Exception("Path error")
    
    # Waiting for Hexrays plugin
    if not ida_hexrays.init_hexrays_plugin():
        logger.error("Hexrays plugin not found, please install Hexrays plugin")
        return
    else:
        logger.info("Hexrays plugin found, version: %s", ida_hexrays.get_hexrays_version())
    
    # Begin decompile
    result = decompile_binary()
    with open(result_file_path, 'w') as f:
        json.dump(result, f, indent=4)   

if __name__ == '__main__':
    idc.auto_wait()
    try:
        main()
    except Exception as e:
        print("Error occured")
        print(traceback.format_exc())
    finally:
        idc.qexit(0)
        pass
    