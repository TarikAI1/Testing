# steganography.py (Updated for delimiter finding)
from PIL import Image
import numpy as np
import qrng # Use our QRNG module
import math
import sys # For stderr
import traceback # For traceback

DELIMITER = b"==STEGAPP_EOF==" # Unique delimiter to mark end of data
DELIMITER_BITS = "".join(format(byte, '08b') for byte in DELIMITER)
SEED_LENGTH_BYTES = 16 # Using 16 bytes for seed

def data_to_binary(data):
    """Convert data (bytes) to a string of binary bits."""
    return "".join(format(byte, '08b') for byte in data)

def binary_to_data(binary_string):
    """Convert a string of binary bits back to bytes."""
    if len(binary_string) % 8 != 0:
         original_len = len(binary_string)
         binary_string = binary_string[:original_len // 8 * 8]
         # Keep the warning as it still indicates potential issues if length is wrong upstream
         print(f"Warning: Binary string length ({original_len}) was not a multiple of 8. Truncated to {len(binary_string)} bits before conversion.", file=sys.stderr)

    if not binary_string:
        return b''

    try:
        byte_list = [int(binary_string[i:i+8], 2) for i in range(0, len(binary_string), 8)]
        return bytes(byte_list)
    except ValueError as e:
        print(f"Error converting binary string chunk to integer: {e}. String: '{binary_string[:80]}...'", file=sys.stderr)
        raise

def embed_data(image_path, data_to_embed, output_path, use_qrng=True):
    """
    Embeds data into an image using LSB steganography.
    Embeds seed first in fixed location, then data in randomized locations
    chosen from the remaining pixels.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        width, height = img.size
        pixels = np.array(img)
        modifiable_pixels = pixels.copy()
        total_pixels = width * height

        # 1. Prepare data
        data_with_delimiter = data_to_embed + DELIMITER
        data_bits = data_to_binary(data_with_delimiter)
        num_data_bits = len(data_bits)
        num_data_pixels_needed = math.ceil(num_data_bits / 3)
        print(f"[Embed] Data size (with delimiter): {len(data_with_delimiter)} bytes = {num_data_bits} bits.")
        print(f"[Embed] Pixels available: {total_pixels}. Data payload needs: {num_data_pixels_needed} pixels.")

        # 2. Get Seed
        seed_bytes = qrng.get_random_bytes(SEED_LENGTH_BYTES)
        if not seed_bytes or len(seed_bytes) != SEED_LENGTH_BYTES:
            print(f"Error: Could not obtain exactly {SEED_LENGTH_BYTES} random bytes for seed.", file=sys.stderr)
            return False
        print(f"[Embed] Generated seed: {seed_bytes.hex()}")

        # 3. Prepare Seed Header
        seed_header_bytes = SEED_LENGTH_BYTES.to_bytes(1, 'big') + seed_bytes
        seed_header_bits = data_to_binary(seed_header_bytes)
        num_seed_header_pixels = math.ceil(len(seed_header_bits) / 3)
        print(f"[Embed] Seed header: {len(seed_header_bytes)} bytes = {len(seed_header_bits)} bits. Needs: {num_seed_header_pixels} pixels.")

        # 4. Capacity Check
        if num_seed_header_pixels + num_data_pixels_needed > total_pixels:
            needed = num_seed_header_pixels + num_data_pixels_needed
            raise ValueError(f"Image not large enough. Needs {needed} pixels ({num_seed_header_pixels} for seed + {num_data_pixels_needed} for data), has {total_pixels}.")

        # 5. Embed Seed Header FIRST
        print(f"[Embed] Embedding seed header into first {num_seed_header_pixels} pixels...")
        seed_pixel_flat_indices_set = set()
        seed_header_idx = 0
        for i in range(num_seed_header_pixels):
            if i >= total_pixels: raise IndexError(f"Attempted to write seed header pixel beyond image bounds ({i} >= {total_pixels})")

            row, col = i // width, i % width
            seed_pixel_flat_indices_set.add(i)

            r, g, b = modifiable_pixels[row, col]
            pixel_modified = False
            if seed_header_idx < len(seed_header_bits):
                bit = int(seed_header_bits[seed_header_idx])
                r = (r & 0xFE) | bit; seed_header_idx += 1; pixel_modified = True
            if seed_header_idx < len(seed_header_bits):
                bit = int(seed_header_bits[seed_header_idx])
                g = (g & 0xFE) | bit; seed_header_idx += 1; pixel_modified = True
            if seed_header_idx < len(seed_header_bits):
                bit = int(seed_header_bits[seed_header_idx])
                b = (b & 0xFE) | bit; seed_header_idx += 1; pixel_modified = True
            if pixel_modified: modifiable_pixels[row, col] = (r, g, b)

        # 6. Identify Available Pixels for Data Payload
        all_pixel_flat_indices = np.arange(total_pixels)
        seed_pixel_flat_indices = np.array(list(seed_pixel_flat_indices_set), dtype=np.int64)
        available_pixel_flat_indices = np.setdiff1d(all_pixel_flat_indices, seed_pixel_flat_indices, assume_unique=True)
        num_available_for_data = len(available_pixel_flat_indices)
        print(f"[Embed] Pixels available for data payload (excluding header): {num_available_for_data}")
        if num_data_pixels_needed > num_available_for_data:
            raise ValueError(f"Not enough available pixels ({num_available_for_data}) for data payload ({num_data_pixels_needed}) after reserving for seed.")

        # 7. Generate Data Pixel Indices from Available Pixels
        try:
            if len(seed_bytes) < 8: seed_bytes_padded = seed_bytes + b'\x00' * (8 - len(seed_bytes))
            else: seed_bytes_padded = seed_bytes
            seed_int = int.from_bytes(seed_bytes_padded[:8], 'big')
            rng = np.random.default_rng(seed=seed_int)
            chosen_flat_indices = rng.choice(available_pixel_flat_indices, size=num_data_pixels_needed, replace=False)
            rows = chosen_flat_indices // width
            cols = chosen_flat_indices % width
            data_pixel_indices = list(zip(rows.tolist(), cols.tolist()))
            print(f"[Embed] Generated {len(data_pixel_indices)} unique indices for data payload.")
        except ValueError as e:
            print(f"Error generating data pixel indices: {e}", file=sys.stderr)
            return False

        # 8. Embed Data Payload
        print(f"[Embed] Embedding {num_data_bits} bits of data payload...")
        data_idx = 0
        for row, col in data_pixel_indices:
            if data_idx >= num_data_bits:
                print(f"Warning: Reached end of data bits ({data_idx}) prematurely.", file=sys.stderr)
                break

            r, g, b = modifiable_pixels[row, col]
            pixel_modified = False
            if data_idx < num_data_bits:
                bit = int(data_bits[data_idx])
                r = (r & 0xFE) | bit; data_idx += 1; pixel_modified = True
            if data_idx < num_data_bits:
                bit = int(data_bits[data_idx])
                g = (g & 0xFE) | bit; data_idx += 1; pixel_modified = True
            if data_idx < num_data_bits:
                bit = int(data_bits[data_idx])
                b = (b & 0xFE) | bit; data_idx += 1; pixel_modified = True
            if pixel_modified: modifiable_pixels[row, col] = (r, g, b)

        # 9. Save the modified image
        stego_image = Image.fromarray(modifiable_pixels, 'RGB')
        save_format = "PNG" if output_path.lower().endswith(".png") else None
        try:
            if save_format:
                stego_image.save(output_path, format=save_format)
            else:
                print(f"Warning: Output path '{output_path}' is not PNG. LSB data may be lost if saved in a lossy format.", file=sys.stderr)
                stego_image.save(output_path, quality=100)
            print(f"[Embed] Data embedded successfully into {output_path}")
            return True
        except Exception as e:
            print(f"Error saving stego image to {output_path}: {e}", file=sys.stderr)
            return False

    except FileNotFoundError:
        print(f"Error: Input image file not found at {image_path}", file=sys.stderr)
        return False
    except ValueError as e:
         print(f"Error embedding data: {e}", file=sys.stderr)
         return False
    except IndexError as e:
         print(f"Error accessing pixel data during embedding (IndexError): {e}", file=sys.stderr)
         return False
    except Exception as e:
        print(f"An unexpected error occurred during embedding: {e}", file=sys.stderr)
        traceback.print_exc()
        return False


def extract_data(image_path):
    """
    Extracts data hidden using the embed_data function. Reads seed first,
    then reads data bits from randomized locations until delimiter is found by searching.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        width, height = img.size
        pixels = np.array(img)
        total_pixels = width * height

        # 1. Extract Seed Header (same as before)
        expected_seed_len = SEED_LENGTH_BYTES
        seed_len_byte_size = 1
        total_seed_header_bytes = seed_len_byte_size + expected_seed_len
        seed_header_bits_len = total_seed_header_bytes * 8
        num_seed_header_pixels = math.ceil(seed_header_bits_len / 3)
        print(f"[Extract] Expecting seed header in first {num_seed_header_pixels} pixels.")
        if num_seed_header_pixels > total_pixels:
            raise ValueError(f"Image is too small ({total_pixels} pixels) to contain the expected seed header ({num_seed_header_pixels} pixels).")

        extracted_seed_header_bits = ""
        seed_pixel_flat_indices_set = set()
        for i in range(num_seed_header_pixels):
             row, col = i // width, i % width
             seed_pixel_flat_indices_set.add(i)
             try: r, g, b = pixels[row, col]; extracted_seed_header_bits += str(r & 1) + str(g & 1) + str(b & 1)
             except IndexError: raise IndexError(f"Failed to read pixel ({row},{col}) for seed header.")

        extracted_seed_header_bits = extracted_seed_header_bits[:seed_header_bits_len]
        try: extracted_seed_header_bytes = binary_to_data(extracted_seed_header_bits)
        except Exception as e: print(f"Failed to convert extracted seed header bits to bytes: {e}", file=sys.stderr); return None
        if len(extracted_seed_header_bytes) != total_seed_header_bytes: print(f"Error: Extracted seed header has wrong size. Expected {total_seed_header_bytes} bytes, got {len(extracted_seed_header_bytes)}.", file=sys.stderr); return None

        extracted_len = int.from_bytes(extracted_seed_header_bytes[0:1], 'big')
        if extracted_len != expected_seed_len: print(f"Warning: Embedded seed length byte ({extracted_len}) doesn't match expected ({expected_seed_len}).", file=sys.stderr)
        seed_bytes = extracted_seed_header_bytes[seed_len_byte_size:]
        if len(seed_bytes) != expected_seed_len: raise ValueError(f"Extracted incorrect number of seed bytes. Expected {expected_seed_len}, got {len(seed_bytes)}.")
        print(f"[Extract] Extracted seed: {seed_bytes.hex()}")

        # 2. Determine Data Pixel Sequence (same as before)
        all_pixel_flat_indices = np.arange(total_pixels)
        seed_pixel_flat_indices = np.array(list(seed_pixel_flat_indices_set), dtype=np.int64)
        seed_pixel_flat_indices = seed_pixel_flat_indices[seed_pixel_flat_indices < total_pixels]
        available_pixel_flat_indices = np.setdiff1d(all_pixel_flat_indices, seed_pixel_flat_indices, assume_unique=True)
        num_available_pixels = len(available_pixel_flat_indices)
        print(f"[Extract] Pixels available for data payload: {num_available_pixels}")
        if num_available_pixels == 0: print("Warning: No pixels available for data extraction after accounting for seed header.", file=sys.stderr); return None

        try:
            if len(seed_bytes) < 8: seed_bytes_padded = seed_bytes + b'\x00' * (8 - len(seed_bytes))
            else: seed_bytes_padded = seed_bytes
            seed_int = int.from_bytes(seed_bytes_padded[:8], 'big')
            rng = np.random.default_rng(seed=seed_int)
            shuffled_available_flat_indices = rng.choice(available_pixel_flat_indices, size=num_available_pixels, replace=False)
            rows = shuffled_available_flat_indices // width
            cols = shuffled_available_flat_indices % width
            data_pixel_indices = list(zip(rows.tolist(), cols.tolist()))
            print(f"[Extract] Generated extraction sequence for {len(data_pixel_indices)} available pixels.")
        except ValueError as e: print(f"Error generating pixel indices for extraction: {e}", file=sys.stderr); return None

        # --- Start NEW Delimiter Finding Logic ---
        # 3. Extract Bits Sequentially and Find Delimiter using find()
        print(f"[Extract] Extracting data bits, searching for delimiter ({len(DELIMITER_BITS)} bits)...")
        extracted_bits = ""
        delimiter_found = False
        bits_to_check_for_delimiter = len(DELIMITER_BITS)
        processed_pixel_count = 0
        # Use a temporary buffer for efficient searching. Size slightly larger than delimiter.
        search_buffer = ""
        SEARCH_BUFFER_LEN = bits_to_check_for_delimiter + 24 # Keep ~3 pixels extra

        for row, col in data_pixel_indices: # Iterate through the determined sequence
            processed_pixel_count += 1
            if row >= height or col >= width:
                print(f"Warning: Skipping invalid pixel index ({row}, {col}) during extraction.", file=sys.stderr)
                continue
            try:
                 r, g, b = pixels[row, col]
                 # Extract 3 bits for this pixel
                 new_bits = str(r & 1) + str(g & 1) + str(b & 1)
                 # Append to the full string and the search buffer
                 extracted_bits += new_bits
                 search_buffer += new_bits

                 # Trim the search buffer from the left to keep it manageable
                 if len(search_buffer) > SEARCH_BUFFER_LEN:
                      search_buffer = search_buffer[-SEARCH_BUFFER_LEN:]

                 # Search for the delimiter within the buffer once it's large enough
                 # Search frequently to find delimiter as soon as possible
                 if len(search_buffer) >= bits_to_check_for_delimiter:
                      found_at_index_in_buffer = search_buffer.find(DELIMITER_BITS)

                      if found_at_index_in_buffer != -1:
                           # Delimiter found in the buffer. Calculate its start position in the *full* extracted_bits stream.
                           buffer_start_in_full_stream = len(extracted_bits) - len(search_buffer)
                           delimiter_start_in_full_stream = buffer_start_in_full_stream + found_at_index_in_buffer

                           print(f"[Extract] Delimiter found starting at bit index {delimiter_start_in_full_stream} after processing {processed_pixel_count} pixels.")
                           delimiter_found = True
                           # The actual data is everything *before* the delimiter started
                           extracted_bits = extracted_bits[:delimiter_start_in_full_stream]
                           break # Stop extracting bits

            except IndexError:
                 print(f"Warning: Failed to read pixel ({row},{col}) during data extraction loop.", file=sys.stderr)
                 continue # Skip this pixel

        # --- End NEW Delimiter Finding Logic ---

        if not delimiter_found:
             # Check if delimiter was perhaps found exactly at the end (missed by buffer logic slightly?) - less likely now
             # This check remains as a fallback, but the find() method should be primary.
             if extracted_bits.endswith(DELIMITER_BITS):
                 print(f"[Extract] Delimiter found exactly at the end after processing {processed_pixel_count} pixels.")
                 delimiter_found = True
                 extracted_bits = extracted_bits[:-bits_to_check_for_delimiter]
             else:
                  print(f"Warning: Reached end of {processed_pixel_count} available data pixels without finding delimiter. Data might be incomplete or corrupted.", file=sys.stderr)
                  if len(extracted_bits) == 0:
                       print("Error: No data payload bits extracted.", file=sys.stderr)
                       return None

        # 4. Convert Bits to Data
        # Check if final bit count is valid *before* conversion
        if len(extracted_bits) % 8 != 0:
             # This indicates a critical logic error somewhere if it happens now.
             print(f"CRITICAL ERROR: Final extracted payload bits length ({len(extracted_bits)}) is not a multiple of 8! This should not happen.", file=sys.stderr)
             # Attempt conversion anyway, binary_to_data will truncate and warn.
             pass

        print(f"[Extract] Converting {len(extracted_bits)} extracted bits to bytes.")
        try:
             extracted_data = binary_to_data(extracted_bits)
        except Exception as e:
             print(f"Failed to convert extracted bits to data: {e}", file=sys.stderr)
             # If conversion fails, data is likely unusable
             traceback.print_exc()
             return None

        print(f"[Extract] Successfully extracted {len(extracted_data)} bytes of data payload.")
        return extracted_data

    except FileNotFoundError:
        print(f"Error: Stego image file not found at {image_path}", file=sys.stderr)
        return None
    except (ValueError, IndexError) as e:
         print(f"Error extracting data (check format/corruption): {e}", file=sys.stderr)
         return None
    except Exception as e:
        print(f"An unexpected error occurred during extraction: {e}", file=sys.stderr)
        traceback.print_exc()
        return None

# Example Usage block (remains the same)
if __name__ == "__main__":
    import os
    if os.path.exists("dummy_input.png"): os.remove("dummy_input.png")
    if os.path.exists("stego_output.png"): os.remove("stego_output.png")
    if os.path.exists("extracted_data.txt"): os.remove("extracted_data.txt")

    print("\n--- [steganography.py] Running Direct Test ---")
    img_size = (150, 100) # WxH
    print(f"Creating dummy image {img_size}...")
    dummy_img = Image.new('RGB', img_size, color = 'white')
    dummy_img.save("dummy_input.png")

    payload_size = 4000
    test_data = b"MSG:" + os.urandom(payload_size) + b":END"
    output_stego_file = "stego_output.png"
    extract_test_file = "extracted_data.txt"
    print(f"Test payload size: {len(test_data)} bytes")

    print("\n--- Embedding ---")
    embed_success = embed_data("dummy_input.png", test_data, output_stego_file, use_qrng=True)

    if embed_success:
        print("\n--- Extracting ---")
        extracted = extract_data(output_stego_file)

        if extracted is not None:
            print(f"\nSuccessfully extracted {len(extracted)} bytes.")
            if extracted == test_data:
                print("Verification SUCCESS: Extracted data matches original.")
            else:
                print("Verification FAILED: Extracted data differs from original.")
                print(f"Original length: {len(test_data)}, Extracted length: {len(extracted)}")
                diff_idx = -1
                for i in range(min(len(test_data), len(extracted))):
                    if test_data[i] != extracted[i]:
                        diff_idx = i
                        break
                if diff_idx != -1:
                     print(f"First difference at index {diff_idx}: Original {test_data[diff_idx]}, Extracted {extracted[diff_idx]}")
                elif len(test_data) != len(extracted):
                     print("Data differs in length.")
        else:
            print("Extraction failed (returned None).")
    else:
        print("Embedding failed.")

    print("\nCleaning up test files...")
    if os.path.exists("dummy_input.png"): os.remove("dummy_input.png")
    if os.path.exists(output_stego_file): os.remove(output_stego_file)
    if os.path.exists(extract_test_file): os.remove(extract_test_file)
    print("--- Test Complete ---")