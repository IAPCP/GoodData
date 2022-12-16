import os
import sys
import magic
from tqdm.auto import tqdm
from pygments.lexers import get_lexer_for_filename

def walk_path(target_path):
    if os.path.isdir(target_path):
        for file_name in os.listdir(target_path):
            yield from walk_path(os.path.join(target_path, file_name))
    else:
        yield target_path

def process_dir(input_path: str, output_path: str):
    for file_path in walk_path(input_path):
        try:
            file_info = magic.from_file(os.path.join(input_path, file_path))
            to_copy = None
            if file_info.startswith("C source") or \
                file_info.startswith("C++ source"):
                to_copy = os.path.join(input_path, file_path)
            elif file_info.startswith("ASCII text"):
                guess_type = get_lexer_for_filename(file_path).name
                if guess_type == "C" or guess_type == "C++":
                    to_copy = os.path.join(input_path, file_path)
            else:
                pass
            if to_copy is not None:
                os.system(f"mkdir -p {os.path.join(output_path, 'src')}")
                os.system(f"cp {os.path.join(input_path, file_path)} {os.path.join(output_path, 'src')}")
                continue
        
            if file_info.startswith("ELF 64-bit LSB executable") or \
                file_info.startswith("current ar archive"):
                os.system(f"mkdir -p {os.path.join(output_path, 'bin')}")
                os.system(f"cp {os.path.join(input_path, file_path)} {os.path.join(output_path, 'bin')}")
        except Exception:
            print(f"Error processing {file_path}")

def process_package(package_path: str, output_path: str):
    process_dir(os.path.join(package_path, "gcc"), output_path)
    process_dir(os.path.join(package_path, "ld"), output_path)

def main(project_path: str, output_path: str):
    for package_name in tqdm(os.listdir(os.path.join(project_path, "packages"))):
        process_package(os.path.join(project_path, "packages", package_name), os.path.join(output_path, package_name))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])