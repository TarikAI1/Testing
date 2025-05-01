# vfs.py (Updated for list_vfs_contents traceback)
import zipfile
import io
import os
import sys
import shutil
import traceback # Import traceback

def create_vfs_archive(file_paths, folder_paths):
    """
    Creates an in-memory ZIP archive containing specified files and folders.
    Returns the archive content as bytes, or None on error.
    """
    print(f"[vfs.py] Attempting to create archive with files: {file_paths}, folders: {folder_paths}")
    zip_buffer = io.BytesIO()
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add individual files
            for file_path in file_paths:
                if os.path.isfile(file_path):
                    archive_name = os.path.basename(file_path)
                    print(f"[vfs.py] Adding file: '{file_path}' as '{archive_name}'")
                    zipf.write(file_path, archive_name)
                else:
                    print(f"[vfs.py] Warning: File not found or is not a file, skipping: {file_path}", file=sys.stderr)

            # Add folders recursively
            for folder_path in folder_paths:
                if os.path.isdir(folder_path):
                    base_folder_name = os.path.basename(folder_path)
                    print(f"[vfs.py] Adding folder: '{folder_path}' as base '{base_folder_name}'")
                    for root, dirs, files in os.walk(folder_path):
                        files = [f for f in files if not f.startswith('.')]
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        for file in files:
                            full_path = os.path.join(root, file)
                            relative_path = os.path.relpath(full_path, folder_path)
                            archive_path = os.path.join(base_folder_name, relative_path)
                            print(f"[vfs.py]   Adding sub-file: '{full_path}' as '{archive_path}'")
                            zipf.write(full_path, archive_path)
                else:
                     print(f"[vfs.py] Warning: Folder not found or is not a directory, skipping: {folder_path}", file=sys.stderr)

        if not zipf.namelist():
             print("[vfs.py] Warning: No files or folders were actually added to the VFS archive.", file=sys.stderr)
             pass

        zip_buffer.seek(0)
        archive_content = zip_buffer.getvalue()
        print(f"[vfs.py] Archive created successfully, size: {len(archive_content)} bytes.")
        return archive_content

    except FileNotFoundError as e:
         print(f"[vfs.py] Error creating VFS archive: File not found - {e}", file=sys.stderr)
         return None
    except Exception as e:
        print(f"[vfs.py] Error creating VFS archive: {e}", file=sys.stderr)
        traceback.print_exc()
        return None

def extract_vfs_archive(archive_bytes, extract_to_dir):
    """
    Extracts an in-memory ZIP archive (given as bytes) to a specified directory.
    Returns True on success, False on error.
    """
    print(f"[vfs.py] Attempting to extract archive ({len(archive_bytes)} bytes) to: {extract_to_dir}")
    if not os.path.exists(extract_to_dir):
        try:
            os.makedirs(extract_to_dir)
            print(f"[vfs.py] Created extraction directory: {extract_to_dir}")
        except OSError as e:
            print(f"[vfs.py] Error creating extraction directory '{extract_to_dir}': {e}", file=sys.stderr)
            return False

    zip_buffer = io.BytesIO(archive_bytes)
    try:
        with zipfile.ZipFile(zip_buffer, 'r') as zipf:
            members_to_extract = zipf.infolist()
            if not members_to_extract:
                 print("[vfs.py] Warning: The VFS archive is empty. Nothing to extract.", file=sys.stderr)
                 return True

            print(f"[vfs.py] Archive contains members: {zipf.namelist()}")

            for member in members_to_extract:
                if member.filename.startswith('/') or member.filename.startswith('\\') or '..' in member.filename.split(os.sep):
                    print(f"[vfs.py] Error: Archive contains potentially unsafe path: {member.filename}", file=sys.stderr)
                    return False

            zipf.extractall(extract_to_dir)

        print(f"[vfs.py] VFS archive extracted successfully to: {extract_to_dir}")
        return True
    except zipfile.BadZipFile:
        print("[vfs.py] Error: Invalid or corrupted VFS archive (BadZipFile).", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[vfs.py] Error extracting VFS archive: {e}", file=sys.stderr)
        traceback.print_exc()
        return False

def list_vfs_contents(archive_bytes):
    """
    Lists the contents (filenames and directories) within the VFS archive bytes.
    Returns a list of strings or None on error.
    """
    if not archive_bytes:
         print("[vfs.py] Error listing contents: Received empty archive bytes.", file=sys.stderr)
         return None

    print(f"[vfs.py] Attempting to list contents of archive ({len(archive_bytes)} bytes)")
    zip_buffer = io.BytesIO(archive_bytes)
    try:
        with zipfile.ZipFile(zip_buffer, 'r') as zipf:
            contents = zipf.namelist()
            print(f"[vfs.py] Archive contents listed: {contents}")
            return contents # Returns empty list [] if zip is valid but empty
    except zipfile.BadZipFile:
        print("[vfs.py] Error: Cannot list contents - Invalid or corrupted VFS archive (BadZipFile).", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[vfs.py] Error listing VFS archive contents: {e}", file=sys.stderr)
        # Ensure traceback is printed for any VFS listing error
        traceback.print_exc() # <<< THIS IS IMPORTANT FOR DEBUGGING
        return None

# Example Usage block
if __name__ == "__main__":
    print("\n--- [vfs.py] Running direct test ---")
    test_base_dir = "temp_vfs_test_artifacts"
    test_folder = os.path.join(test_base_dir, "folder1")
    test_file1 = os.path.join(test_base_dir, "file1.txt")
    test_file2 = os.path.join(test_folder, "file2.bin")
    extract_dir = "temp_vfs_extracted_test"

    if os.path.exists(test_base_dir): shutil.rmtree(test_base_dir)
    if os.path.exists(extract_dir): shutil.rmtree(extract_dir)

    os.makedirs(test_folder, exist_ok=True)
    with open(test_file1, "w") as f: f.write("Hello VFS Test")
    with open(test_file2, "wb") as f: f.write(b"\x01\x02\x03\x04\xFE\xFF")
    print(f"[vfs.py] Test files created in '{test_base_dir}'")

    archive = create_vfs_archive([test_file1], [test_folder])
    if archive:
        print(f"[vfs.py] Test archive created, size: {len(archive)} bytes")

        print("\n[vfs.py] Listing test archive contents:")
        contents = list_vfs_contents(archive)
        if contents is not None: # Check explicitly for None on error
            for item in contents:
                print(f"- {item}")
        else:
            print("[vfs.py] Failed to list contents.")

        print("\n[vfs.py] Extracting test archive:")
        if not os.path.exists(extract_dir): os.mkdir(extract_dir)
        success = extract_vfs_archive(archive, extract_dir)
        print(f"[vfs.py] Test extraction successful: {success}")
        if success:
            print(f"[vfs.py] Check contents in '{extract_dir}' folder.")
            extracted_check_file = os.path.join(extract_dir, os.path.basename(test_file1)) # Check needs correct path inside zip
            # To check content correctly, need the name as stored in the zip:
            check_name_in_zip = os.path.basename(test_file1) # As it was added directly
            extracted_check_file = os.path.join(extract_dir, check_name_in_zip)

            if os.path.exists(extracted_check_file):
                with open(extracted_check_file, "r") as f_check:
                    content = f_check.read()
                    print(f"[vfs.py] Content check for {check_name_in_zip}: '{content}'")
            else:
                 print(f"[vfs.py] Check file '{check_name_in_zip}' not found in extraction at '{extracted_check_file}'.")

    else:
        print("[vfs.py] Failed to create test archive.")

    print("\n[vfs.py] Cleaning up test directories...")
    if os.path.exists(test_base_dir):
        shutil.rmtree(test_base_dir)
        print(f"[vfs.py] Cleaned up '{test_base_dir}'.")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
        print(f"[vfs.py] Cleaned up '{extract_dir}'.")

    print("--- [vfs.py] Test Complete ---")