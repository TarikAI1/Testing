# main_app.py
import customtkinter as ctk
from tkinter import filedialog, messagebox, Listbox, Scrollbar, MULTIPLE, END
import os
import threading # To avoid freezing GUI during processing

# Import our modules
import vfs
import steganography

# Basic App Setup
ctk.set_appearance_mode("System") # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue") # Themes: "blue" (default), "green", "dark-blue"

class SteganoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("SteganoVFS - Quantum Enhanced Steganography")
        self.geometry(f"{1100}x{700}") # Adjusted size

        # --- State Variables ---
        self.input_image_path = None
        self.output_image_path = None
        self.files_to_embed = []
        self.folders_to_embed = []
        self.stego_image_for_extraction = None
        self.extracted_vfs_data = None # Store extracted VFS bytes here

        # --- Main Layout Frames ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0) # Row for attribution

        # Left Frame (Embedding)
        self.left_frame = ctk.CTkFrame(self, corner_radius=10)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)
        # Configure rows as needed within the frame

        # Right Frame (Extraction / VFS View)
        self.right_frame = ctk.CTkFrame(self, corner_radius=10)
        self.right_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        # Configure rows as needed

        # Attribution Label
        self.attribution_label = ctk.CTkLabel(self, text="Created by Tarik Aissaoui", font=ctk.CTkFont(size=18))
        self.attribution_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="s")


        # --- Populate Frames ---
        self._create_embed_widgets()
        self._create_extract_widgets()
        self._create_vfs_view_widgets() # VFS view in the right frame

    # --- Widget Creation Methods ---
    def _create_embed_widgets(self):
        frame = self.left_frame
        frame.grid_rowconfigure(5, weight=1) # Give space to listbox

        title = ctk.CTkLabel(frame, text="Embed VFS into Image", font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Input Image
        self.input_image_label = ctk.CTkLabel(frame, text="No Input Image Selected")
        self.input_image_label.grid(row=1, column=0, padx=20, pady=5)
        input_image_button = ctk.CTkButton(frame, text="Select Input Image", command=self.select_input_image)
        input_image_button.grid(row=2, column=0, padx=20, pady=5)

        # Files/Folders Selection
        select_files_button = ctk.CTkButton(frame, text="Add Files to VFS", command=self.add_files)
        select_files_button.grid(row=3, column=0, padx=20, pady=(15, 5))
        select_folder_button = ctk.CTkButton(frame, text="Add Folder to VFS", command=self.add_folder)
        select_folder_button.grid(row=4, column=0, padx=20, pady=5)

        # Listbox for selected items
        self.vfs_items_listbox = Listbox(frame, selectmode=MULTIPLE, bg="#2B2B2B", fg="white", borderwidth=0, highlightthickness=0)
        self.vfs_items_listbox.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")
        # Add scrollbar if needed (later)
        remove_item_button = ctk.CTkButton(frame, text="Remove Selected", command=self.remove_selected_items)
        remove_item_button.grid(row=6, column=0, padx=20, pady=5)
        clear_items_button = ctk.CTkButton(frame, text="Clear All", command=self.clear_vfs_items)
        clear_items_button.grid(row=7, column=0, padx=20, pady=5)

        # Output Path & Embed Button
        self.output_path_label = ctk.CTkLabel(frame, text="Output: Not Set")
        self.output_path_label.grid(row=8, column=0, padx=20, pady=5)
        output_path_button = ctk.CTkButton(frame, text="Set Output Image Path", command=self.set_output_path)
        output_path_button.grid(row=9, column=0, padx=20, pady=5)

        self.embed_button = ctk.CTkButton(frame, text="Embed VFS", command=self.start_embedding_thread, font=ctk.CTkFont(weight="bold"))
        self.embed_button.grid(row=10, column=0, padx=20, pady=(15, 20))

    def _create_extract_widgets(self):
        # Put extraction selection at the top of the right frame
        frame = self.right_frame

        title = ctk.CTkLabel(frame, text="Extract VFS from Image", font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.extract_image_label = ctk.CTkLabel(frame, text="No Stego Image Selected")
        self.extract_image_label.grid(row=1, column=0, padx=20, pady=5)
        extract_image_button = ctk.CTkButton(frame, text="Select Stego Image", command=self.select_stego_image)
        extract_image_button.grid(row=2, column=0, padx=20, pady=5)

        # --- Status/Progress (optional, add later if needed) ---
        self.status_label = ctk.CTkLabel(frame, text="")
        # self.status_label.grid(...) # Decide placement

    def _create_vfs_view_widgets(self):
         # VFS viewer below extraction selection in the right frame
        frame = self.right_frame
        frame.grid_rowconfigure(5, weight=1) # Give listbox space

        vfs_title = ctk.CTkLabel(frame, text="VFS Contents Viewer", font=ctk.CTkFont(size=16, weight="bold"))
        vfs_title.grid(row=3, column=0, padx=20, pady=(20, 5))

        # Listbox for VFS contents
        self.vfs_content_listbox = Listbox(frame, bg="#2B2B2B", fg="white", borderwidth=0, highlightthickness=0)
        self.vfs_content_listbox.grid(row=4, column=0, padx=20, pady=5, sticky="nsew")
        # Add scrollbar (optional)
        vfs_scrollbar = Scrollbar(self.vfs_content_listbox, orient="vertical", command=self.vfs_content_listbox.yview)
        #vfs_scrollbar.pack(side="right", fill="y") # Example packing
        self.vfs_content_listbox.config(yscrollcommand=vfs_scrollbar.set)

        self.extract_vfs_button = ctk.CTkButton(frame, text="Extract VFS Content", command=self.start_vfs_extraction_thread, state="disabled") # Disabled initially
        self.extract_vfs_button.grid(row=5, column=0, padx=20, pady=(10, 20))


    # --- Action Methods ---
    def select_input_image(self):
        path = filedialog.askopenfilename(
            title="Select Input Image",
            filetypes=[("Image Files", "*.png *.bmp *.tiff"), ("All Files", "*.*")] # Recommend lossless
        )
        if path:
            self.input_image_path = path
            self.input_image_label.configure(text=f"Input: ...{os.path.basename(path)}")
            print(f"Selected input image: {path}")
            # Automatically suggest output path based on input
            base, ext = os.path.splitext(path)
            suggested_output = f"{base}_stego.png" # Always suggest PNG
            self.output_image_path = suggested_output
            self.output_path_label.configure(text=f"Output: ...{os.path.basename(suggested_output)}")

    def add_files(self):
        paths = filedialog.askopenfilenames(title="Select Files to Add")
        if paths:
            for path in paths:
                if path not in self.files_to_embed and path not in [f[1] for f in self.folders_to_embed]: # Avoid duplicates
                    self.files_to_embed.append(path)
                    self.vfs_items_listbox.insert(END, f"[F] {os.path.basename(path)}")
            print(f"Files to embed: {self.files_to_embed}")

    def add_folder(self):
         path = filedialog.askdirectory(title="Select Folder to Add")
         if path:
             # Check if parent or child of existing folders/files to avoid redundancy/cycles (simple check)
             is_redundant = False
             for f_path in self.files_to_embed:
                  if f_path.startswith(path + os.sep):
                       print(f"Skipping folder '{path}' as it contains already selected file '{f_path}'")
                       is_redundant = True; break
             if not is_redundant:
                 for fol_path in self.folders_to_embed:
                     if path.startswith(fol_path + os.sep): # Adding subfolder of existing
                          print(f"Skipping folder '{path}' as it's inside already selected folder '{fol_path}'")
                          is_redundant = True; break
                     if fol_path.startswith(path + os.sep): # Adding parent of existing
                         print(f"Skipping folder '{path}' as it contains already selected folder '{fol_path}'")
                         is_redundant = True; break

             if not is_redundant and path not in self.folders_to_embed:
                 self.folders_to_embed.append(path)
                 self.vfs_items_listbox.insert(END, f"[D] {os.path.basename(path)}")
                 print(f"Folders to embed: {self.folders_to_embed}")


    def remove_selected_items(self):
        selected_indices = self.vfs_items_listbox.curselection()
        if not selected_indices: return

        # Get items text before removing
        items_to_remove_text = [self.vfs_items_listbox.get(i) for i in selected_indices]

        # Remove from listbox (iterate backwards to avoid index shifting)
        for i in sorted(selected_indices, reverse=True):
            self.vfs_items_listbox.delete(i)

        # Remove from internal lists
        new_files = []
        new_folders = []
        for f in self.files_to_embed:
            if f"[F] {os.path.basename(f)}" not in items_to_remove_text:
                new_files.append(f)
        for d in self.folders_to_embed:
             if f"[D] {os.path.basename(d)}" not in items_to_remove_text:
                 new_folders.append(d)
        self.files_to_embed = new_files
        self.folders_to_embed = new_folders
        print(f"Updated files: {self.files_to_embed}")
        print(f"Updated folders: {self.folders_to_embed}")


    def clear_vfs_items(self):
        self.vfs_items_listbox.delete(0, END)
        self.files_to_embed = []
        self.folders_to_embed = []
        print("Cleared VFS items.")

    def set_output_path(self):
        path = filedialog.asksaveasfilename(
            title="Save Stego Image As",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
            initialfile=os.path.basename(self.output_image_path) if self.output_image_path else "stego_output.png"
        )
        if path:
             # Ensure it ends with .png for our LSB method
             if not path.lower().endswith(".png"):
                  path += ".png"
             self.output_image_path = path
             self.output_path_label.configure(text=f"Output: ...{os.path.basename(path)}")
             print(f"Set output path: {path}")

    def select_stego_image(self):
        path = filedialog.askopenfilename(
            title="Select Stego Image for Extraction",
            filetypes=[("Image Files", "*.png *.bmp *.tiff"), ("All Files", "*.*")]
        )
        if path:
            self.stego_image_for_extraction = path
            self.extract_image_label.configure(text=f"Stego Img: ...{os.path.basename(path)}")
            print(f"Selected stego image: {path}")
            # Clear previous VFS view and disable extraction button until data is loaded
            self.vfs_content_listbox.delete(0, END)
            self.extracted_vfs_data = None
            self.extract_vfs_button.configure(state="disabled")
            # Automatically trigger data extraction and VFS listing
            self.start_data_extraction_thread() # Separate thread for potentially long op

    # --- Threading Wrappers ---
    def start_embedding_thread(self):
         if not self.input_image_path:
             messagebox.showerror("Error", "Please select an input image.")
             return
         if not self.output_image_path:
              messagebox.showerror("Error", "Please set an output image path.")
              return
         if not self.files_to_embed and not self.folders_to_embed:
              messagebox.showerror("Error", "Please add files or folders to the VFS.")
              return

         # Disable button during processing
         self.embed_button.configure(state="disabled", text="Embedding...")
         # Run in thread
         thread = threading.Thread(target=self.perform_embedding, daemon=True)
         thread.start()

    def start_data_extraction_thread(self):
        if not self.stego_image_for_extraction:
             # This shouldn't happen due to UI flow, but check anyway
             messagebox.showerror("Error", "No stego image selected for data extraction.")
             return
        # Optionally show some "Loading..." state
        print("Starting data extraction from image...")
        thread = threading.Thread(target=self.perform_data_extraction, daemon=True)
        thread.start()

    def start_vfs_extraction_thread(self):
        if not self.extracted_vfs_data:
            messagebox.showerror("Error", "No VFS data loaded or extracted yet.")
            return
        extract_to = filedialog.askdirectory(title="Select Directory to Extract VFS Contents")
        if not extract_to:
             return

        # Disable button
        self.extract_vfs_button.configure(state="disabled", text="Extracting...")
        thread = threading.Thread(target=self.perform_vfs_extraction, args=(extract_to,), daemon=True)
        thread.start()


    # --- Core Logic Execution (called from threads) ---
    def perform_embedding(self):
        try:
            print("Creating VFS archive...")
            archive_bytes = vfs.create_vfs_archive(self.files_to_embed, self.folders_to_embed)

            if not archive_bytes:
                messagebox.showerror("Error", "Failed to create VFS archive. Check console for details.")
                self.embed_button.configure(state="normal", text="Embed VFS") # Re-enable button
                return

            print(f"VFS archive created ({len(archive_bytes)} bytes). Starting embedding...")
            # Set status?
            success = steganography.embed_data(
                self.input_image_path,
                archive_bytes,
                self.output_image_path,
                use_qrng=True # Or add a checkbox to control this
            )

            if success:
                messagebox.showinfo("Success", f"VFS embedded successfully into\n{os.path.basename(self.output_image_path)}")
                print("Embedding finished successfully.")
            else:
                messagebox.showerror("Error", "Failed to embed VFS into image. Check console for details (e.g., image size).")
                print("Embedding failed.")

        except Exception as e:
             messagebox.showerror("Embedding Error", f"An unexpected error occurred: {e}")
             print(f"Embedding exception: {e}")
             # import traceback; traceback.print_exc() # For debugging

        finally:
            # Re-enable button (ensure this runs even if errors occur)
            self.embed_button.configure(state="normal", text="Embed VFS")


    def perform_data_extraction(self):
        """Extracts raw data block from stego image, then lists VFS."""
        try:
            print(f"Attempting to extract data from {self.stego_image_for_extraction}")
            extracted_data = steganography.extract_data(self.stego_image_for_extraction)

            if extracted_data:
                print(f"Successfully extracted {len(extracted_data)} bytes.")
                self.extracted_vfs_data = extracted_data # Store the raw bytes

                # Now list contents
                print("Listing VFS contents...")
                vfs_content = vfs.list_vfs_contents(self.extracted_vfs_data)

                # Update GUI listbox (must be done via schedule)
                def update_gui():
                     self.vfs_content_listbox.delete(0, END)
                     if vfs_content:
                          for item in vfs_content:
                               self.vfs_content_listbox.insert(END, item)
                          self.extract_vfs_button.configure(state="normal") # Enable extraction
                          print("VFS contents listed in GUI.")
                     else:
                          self.vfs_content_listbox.insert(END, "Failed to list VFS contents (invalid archive?).")
                          self.extract_vfs_button.configure(state="disabled")
                          messagebox.showwarning("VFS Warning", "Extracted data, but could not read it as a VFS archive. It might be corrupted or not a VFS.")

                self.after(0, update_gui) # Schedule GUI update from main thread

            else:
                print("Failed to extract any data from the image.")
                self.extracted_vfs_data = None
                # Update GUI (schedule)
                def update_gui_fail():
                    self.vfs_content_listbox.delete(0, END)
                    self.vfs_content_listbox.insert(END, "No data found or extraction failed.")
                    self.extract_vfs_button.configure(state="disabled")
                    messagebox.showerror("Extraction Error", "Could not extract data from the selected image. It might not contain hidden data or is corrupted.")
                self.after(0, update_gui_fail)


        except Exception as e:
             print(f"Data extraction exception: {e}")
             # import traceback; traceback.print_exc() # For debugging
             self.extracted_vfs_data = None
             # Update GUI (schedule)
             def update_gui_exc():
                 self.vfs_content_listbox.delete(0, END)
                 self.vfs_content_listbox.insert(END, "An error occurred during extraction.")
                 self.extract_vfs_button.configure(state="disabled")
                 messagebox.showerror("Extraction Error", f"An unexpected error occurred during data extraction: {e}")
             self.after(0, update_gui_exc)


    def perform_vfs_extraction(self, extract_to_dir):
         """Extracts the loaded VFS data to the chosen directory."""
         try:
              print(f"Extracting VFS content to: {extract_to_dir}")
              success = vfs.extract_vfs_archive(self.extracted_vfs_data, extract_to_dir)

              # Update GUI (schedule)
              def update_gui():
                  if success:
                      messagebox.showinfo("Extraction Complete", f"VFS contents extracted successfully to:\n{extract_to_dir}")
                      print("VFS extraction successful.")
                  else:
                       messagebox.showerror("VFS Extraction Error", "Failed to extract the VFS archive. It might be corrupted. Check console.")
                       print("VFS extraction failed.")
                  # Re-enable button
                  self.extract_vfs_button.configure(state="normal", text="Extract VFS Content")

              self.after(0, update_gui)

         except Exception as e:
              print(f"VFS extraction exception: {e}")
              # import traceback; traceback.print_exc() # For debugging
              # Update GUI (schedule)
              def update_gui_exc():
                  messagebox.showerror("VFS Extraction Error", f"An unexpected error occurred: {e}")
                  self.extract_vfs_button.configure(state="normal", text="Extract VFS Content")
              self.after(0, update_gui_exc)


# --- Main Execution ---
if __name__ == "__main__":
    app = SteganoApp()
    app.mainloop()