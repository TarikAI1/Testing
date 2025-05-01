# main_app.py
# Center Preview button horizontally within its section, keep Textbox preview

import tkinter as tk
import tkinter.font as tkFont
# No ttk import needed
from tkinter import filedialog, messagebox, simpledialog
import customtkinter # Using CustomTkinter
import os
import platform # To check OS for maximizing window
import threading
import traceback
import io
import tarfile

# Import necessary modules from your project
import steganography

# --- Constants for Styling ---
FONT_FAMILY_PRIMARY = "Segoe UI"; FONT_FAMILY_FALLBACK = "Arial"
FONT_MONO_PRIMARY = "Consolas"; FONT_MONO_FALLBACK = "Courier New"
DEFAULT_FONT_SIZE = 13; HEADER_FONT_SIZE = 16; STATUS_FONT_SIZE = 11
CREDIT_FONT_SIZE = DEFAULT_FONT_SIZE + 3; PREVIEW_ITEM_FONT_SIZE = DEFAULT_FONT_SIZE -1

# --- Dark Theme Color Palette ---
COLORS = {
    'frame_bg': ["#2B2B2B", "#2B2B2B"], 'widget_bg': ["#343638", "#343638"],
    'button': ["#3E81AD", "#3E81AD"], 'button_hover': ["#2C5F8C", "#2C5F8C"],
    'button_text': ["#DCE4EE", "#DCE4EE"], 'accent': ["#3E81AD", "#3E81AD"],
    'text': ["#DCE4EE", "#DCE4EE"], 'text_secondary': ["#A0A0A0", "#A0A0A0"],
    'disabled_fg': ["#7A7A7A", "#7A7A7A"], 'disabled_button_bg': ["#424242", "#424242"],
    'list_tree_bg': "#2E2E2E", 'list_tree_fg': "#DCE4EE",
    'select_bg': "#2A5E84", 'select_fg': "#FFFFFF",
    'border': "#565B5E", 'success': '#8CDB7E', 'error': '#E57373',
    'warning': '#FFB74D', 'info': '#64B5F6',
    'switch_progress': ["#569CD6", "#569CD6"],
}
# --- End of Constants Block ---


class SteganoVFSApp:
    def __init__(self, master):
        self.master = master
        master.title("SteganoVFS")
        self.initial_width = 800
        self.initial_height = 750
        master.minsize(700, 650)
        master.geometry(f"{self.initial_width}x{self.initial_height}")

        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")

        # --- Define Fonts ---
        try: active_font_family = FONT_FAMILY_PRIMARY; tkFont.Font(family=active_font_family).actual()
        except tk.TclError: active_font_family = FONT_FAMILY_FALLBACK
        print(f"Using main font family: {active_font_family}")
        try: active_mono_family = FONT_MONO_PRIMARY; tkFont.Font(family=active_mono_family).actual()
        except tk.TclError: active_mono_family = FONT_MONO_FALLBACK
        print(f"Using mono font family: {active_mono_family}")
        self.font_default = customtkinter.CTkFont(family=active_font_family, size=DEFAULT_FONT_SIZE)
        self.font_header = customtkinter.CTkFont(family=active_font_family, size=HEADER_FONT_SIZE, weight="bold")
        self.font_status = customtkinter.CTkFont(family=active_font_family, size=STATUS_FONT_SIZE)
        self.font_credit = customtkinter.CTkFont(family=active_font_family, size=CREDIT_FONT_SIZE)
        self.font_preview = customtkinter.CTkFont(family=active_mono_family, size=PREVIEW_ITEM_FONT_SIZE)

        # --- Instance Variables ---
        self.input_image_path = ""
        self.files_to_embed = []
        self.folders_to_embed = []
        self.use_qrng_flag = tk.BooleanVar(value=True)

        # --- GUI Structure ---
        master.columnconfigure(0, weight=1)
        master.rowconfigure(4, weight=1) # Preview row expands
        for i in range(9): master.grid_rowconfigure(i, pad=5); master.grid_columnconfigure(0, pad=10)

        # Frame definitions
        input_frame=customtkinter.CTkFrame(master, corner_radius=10); input_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5)); input_frame.columnconfigure(0, weight=1)
        qrng_frame=customtkinter.CTkFrame(master, corner_radius=10); qrng_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        embed_frame=customtkinter.CTkFrame(master, corner_radius=10); embed_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5); embed_frame.columnconfigure(0, weight=1)
        sep1=customtkinter.CTkFrame(master, height=2, fg_color=COLORS['border'], corner_radius=0); sep1.grid(row=3, column=0, sticky="ew", padx=40, pady=10)
        preview_frame=customtkinter.CTkFrame(master, corner_radius=10); preview_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5); preview_frame.columnconfigure(0, weight=1); preview_frame.rowconfigure(2, weight=1) # Textbox row (now 2) expands
        sep2=customtkinter.CTkFrame(master, height=2, fg_color=COLORS['border'], corner_radius=0); sep2.grid(row=5, column=0, sticky="ew", padx=40, pady=10)
        action_frame=customtkinter.CTkFrame(master, fg_color="transparent"); action_frame.grid(row=6, column=0, pady=5); action_frame.grid_columnconfigure(0, weight=1)
        status_frame=customtkinter.CTkFrame(master, fg_color="transparent"); status_frame.grid(row=7, column=0, sticky="ew", padx=10, pady=(5,0)); status_frame.columnconfigure(0, weight=1)
        credit_frame=customtkinter.CTkFrame(master, fg_color="transparent"); credit_frame.grid(row=8, column=0, sticky="ew", padx=10, pady=(5,10)); credit_frame.columnconfigure(0, weight=1)

        # --- Input Image Selection (in input_frame) ---
        input_inner_frame = customtkinter.CTkFrame(input_frame, fg_color="transparent"); input_inner_frame.pack(fill="x", padx=15, pady=10); input_inner_frame.columnconfigure(0, weight=1)
        input_label = customtkinter.CTkLabel(input_inner_frame, text="Input Image:", font=self.font_header); input_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,5))
        self.input_image_entry = customtkinter.CTkEntry(input_inner_frame, placeholder_text="Select image file...", height=35, font=self.font_default, border_width=1, border_color=COLORS['border'])
        self.input_image_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.input_image_button = customtkinter.CTkButton(input_inner_frame, text="Browse...", width=100, height=35, font=self.font_default, command=self.select_input_image)
        self.input_image_button.grid(row=1, column=1, sticky="e")

        # --- QRNG Switch (in qrng_frame) ---
        qrng_inner_frame = customtkinter.CTkFrame(qrng_frame, fg_color="transparent"); qrng_inner_frame.pack(padx=15, pady=10, anchor='w')
        self.qrng_switch = customtkinter.CTkSwitch(qrng_inner_frame, text="Use Quantum RNG (Requires Internet)", font=self.font_default, variable=self.use_qrng_flag, onvalue=True, offvalue=False, command=self.toggle_qrng, progress_color=COLORS['switch_progress'])
        self.qrng_switch.pack(side=tk.LEFT)

        # --- Files/Folders to Embed Selection (in embed_frame) ---
        embed_inner_frame = customtkinter.CTkFrame(embed_frame, fg_color="transparent"); embed_inner_frame.pack(fill="both", expand=False, padx=15, pady=10)
        embed_inner_frame.columnconfigure(0, weight=1);
        embed_label = customtkinter.CTkLabel(embed_inner_frame, text="Files & Folders to Embed:", font=self.font_header); embed_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0,10))
        listbox_frame = customtkinter.CTkFrame(embed_inner_frame, fg_color="transparent", border_width=1, border_color=COLORS['border'], corner_radius=5)
        listbox_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        listbox_frame.columnconfigure(0, weight=1); listbox_frame.rowconfigure(0, weight=0)
        self.embed_listbox = tk.Listbox(listbox_frame, height=5, selectmode=tk.EXTENDED, font=(active_font_family, DEFAULT_FONT_SIZE), background=COLORS['list_tree_bg'], foreground=COLORS['list_tree_fg'], selectbackground=COLORS['select_bg'], selectforeground=COLORS['select_fg'], borderwidth=0, relief=tk.FLAT, highlightthickness=0)
        self.embed_listbox.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        embed_scrollbar = customtkinter.CTkScrollbar(listbox_frame, command=self.embed_listbox.yview, button_color=COLORS['button'], button_hover_color=COLORS['button_hover'])
        embed_scrollbar.grid(row=0, column=1, sticky="ns", pady=1, padx=(0,1))
        self.embed_listbox.configure(yscrollcommand=embed_scrollbar.set)
        embed_buttons_frame = customtkinter.CTkFrame(embed_inner_frame, fg_color="transparent")
        embed_buttons_frame.grid(row=2, column=0, columnspan=3, sticky="", pady=(5,0)) # Centered frame
        self.add_files_button = customtkinter.CTkButton(embed_buttons_frame, text="Add Files", height=35, font=self.font_default, command=self.add_files); self.add_files_button.pack(side=tk.LEFT, padx=10)
        self.add_folder_button = customtkinter.CTkButton(embed_buttons_frame, text="Add Folder", height=35, font=self.font_default, command=self.add_folder); self.add_folder_button.pack(side=tk.LEFT, padx=10)
        self.remove_button = customtkinter.CTkButton(embed_buttons_frame, text="Remove", height=35, font=self.font_default, command=self.remove_selected, fg_color=COLORS['error'], hover_color='#AB5454'); self.remove_button.pack(side=tk.LEFT, padx=10)

        # --- VFS Preview Area (in preview_frame) ---
        preview_inner_frame = customtkinter.CTkFrame(preview_frame, fg_color="transparent")
        preview_inner_frame.pack(fill="both", expand=True, padx=15, pady=(5,0))
        preview_inner_frame.columnconfigure(0, weight=1) # Column 0 for label/textbox takes weight
        preview_inner_frame.columnconfigure(1, weight=0) # Column 1 for button takes minimum space
        preview_inner_frame.rowconfigure(1, weight=1) # Textbox row expands

        preview_label = customtkinter.CTkLabel(preview_inner_frame, text="VFS Contents Preview", font=self.font_header)
        # *** Grid label in row 0, column 0, sticky W ***
        preview_label.grid(row=0, column=0, sticky="w", pady=(0,5), padx=(0, 10))

        # *** Preview Button in row 0, column 1, sticky E ***
        self.preview_button = customtkinter.CTkButton(preview_inner_frame, text="Preview", height=30, width=100,
                                                      font=self.font_default, command=self.start_preview_thread, state=tk.DISABLED)
        self.preview_button.grid(row=0, column=1, sticky="e", pady=(0, 5))

        # CTkTextbox for Preview - Row 1, Spanning 2 columns
        self.preview_textbox = customtkinter.CTkTextbox(
            preview_inner_frame,
            font=self.font_preview, # Use mono font
            corner_radius=5,
            border_width=1, border_color=COLORS['border'],
            fg_color=COLORS['list_tree_bg'], text_color=COLORS['list_tree_fg'],
            wrap="none", state=tk.DISABLED
        )
        self.preview_textbox.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 5))


        # --- Action Buttons (in action_frame) ---
        action_button_frame = customtkinter.CTkFrame(action_frame, fg_color="transparent"); action_button_frame.pack()
        self.embed_button = customtkinter.CTkButton(action_button_frame, text="Embed Data", width=160, height=45, font=self.font_header, command=self.start_embed_thread); self.embed_button.pack(side=tk.LEFT, padx=15, pady=10)
        self.extract_button = customtkinter.CTkButton(action_button_frame, text="Extract Data", width=160, height=45, font=self.font_header, command=self.start_extract_thread); self.extract_button.pack(side=tk.LEFT, padx=15, pady=10)

        # --- Status Label (in status_frame) ---
        self.status_label = customtkinter.CTkLabel(status_frame, text="Status: Ready", font=self.font_status, text_color=COLORS['info'], anchor="w"); self.status_label.grid(row=0, column=0, sticky="ew", padx=10)

        # --- Credit Label (in credit_frame) ---
        self.credit_label = customtkinter.CTkLabel(credit_frame, text="Created by Tarik Aissaoui", font=self.font_credit, text_color=COLORS['text_secondary'], anchor="center"); self.credit_label.grid(row=0, column=0, sticky="ew")

        # --- Instantiate Steganography Handler ---
        self.stego_handler = steganography.Steganography(verbose=True)


    # --- GUI Update & Control Methods ---
    def select_input_image(self):
        path = filedialog.askopenfilename(parent=self.master, title="Select Input Image", filetypes=[("Image Files", "*.png *.bmp *.tiff"), ("All Files", "*.*")])
        if path:
            self.input_image_path = path; self.input_image_entry.delete(0, tk.END); self.input_image_entry.insert(0, path)
            self.update_status(f"Selected: {os.path.basename(path)}", "info")
            self.preview_button.configure(state=tk.NORMAL);
            self.clear_preview_textbox() # Use textbox clear

    def toggle_qrng(self):
        is_on = self.use_qrng_flag.get()
        status = "ON" if is_on else "OFF (using fallback)"
        self._log(f"Quantum RNG toggled {status}")
        self.update_status(f"Quantum RNG is {status}", "info")

    def add_files(self):
        files = filedialog.askopenfilenames(parent=self.master, title="Select Files to Embed")
        if files:
            added_count = 0
            for file in files:
                already_exists = any(f == file for f in self.files_to_embed) or any(f == file for f in self.folders_to_embed)
                if not already_exists and os.path.exists(file):
                    self.files_to_embed.append(file); self.embed_listbox.insert(tk.END, f"[F] {os.path.basename(file)}"); added_count += 1
            if added_count > 0: self.update_status(f"Added {added_count} file(s).", "info")

    def add_folder(self):
        folder = filedialog.askdirectory(parent=self.master, title="Select Folder to Embed", mustexist=True)
        if folder:
             already_exists = any(f == folder for f in self.files_to_embed) or any(f == folder for f in self.folders_to_embed)
             if not already_exists:
                    self.folders_to_embed.append(folder); self.embed_listbox.insert(tk.END, f"[D] {os.path.basename(folder)}")
                    self.update_status(f"Added folder: {os.path.basename(folder)}", "info")

    def remove_selected(self):
        selected_indices = self.embed_listbox.curselection()
        if not selected_indices: return
        items_to_remove_from_files, items_to_remove_from_folders, listbox_items_to_delete = [], [], []
        for i in selected_indices:
            item_text = self.embed_listbox.get(i); listbox_items_to_delete.append(i); base_name = item_text[4:]
            if item_text.startswith("[F] "): found = next((f for f in self.files_to_embed if os.path.basename(f) == base_name), None);
            if found: items_to_remove_from_files.append(found)
            elif item_text.startswith("[D] "): found = next((f for f in self.folders_to_embed if os.path.basename(f) == base_name), None);
            if found: items_to_remove_from_folders.append(found)
        for item in items_to_remove_from_files:
             if item in self.files_to_embed: self.files_to_embed.remove(item)
        for item in items_to_remove_from_folders:
             if item in self.folders_to_embed: self.folders_to_embed.remove(item)
        for i in sorted(listbox_items_to_delete, reverse=True): self.embed_listbox.delete(i)
        removed_count = len(items_to_remove_from_files) + len(items_to_remove_from_folders)
        if removed_count > 0: self.update_status(f"Removed {removed_count} item(s).", "info")

    # Original update_status
    def update_status(self, message, color_key="info"):
        color = COLORS.get(color_key.lower(), COLORS['text'])
        update_func = lambda msg=message, clr=color: self.status_label.configure(text=f"Status: {msg}", text_color=clr)
        self.master.after(0, update_func)

    def set_gui_state(self, state):
        gui_state = "normal" if state == 'normal' else "disabled"
        try:
             self.input_image_entry.configure(state=gui_state)
             self.input_image_button.configure(state=gui_state)
             self.qrng_switch.configure(state=gui_state)
             self.add_files_button.configure(state=gui_state)
             self.add_folder_button.configure(state=gui_state)
             self.remove_button.configure(state=gui_state)
             listbox_tk_state = tk.NORMAL if state == 'normal' else tk.DISABLED
             if hasattr(self, 'embed_listbox') and self.embed_listbox.winfo_exists():
                 self.embed_listbox.configure(state=listbox_tk_state,
                     background=COLORS['list_tree_bg'] if state == 'normal' else COLORS['frame_bg'][1],
                     foreground=COLORS['list_tree_fg'] if state == 'normal' else COLORS['disabled_fg'] )
             self.embed_button.configure(state=gui_state)
             self.extract_button.configure(state=gui_state)
             preview_state = "disabled"
             if state == 'normal' and self.input_image_path: preview_state = "normal"
             if hasattr(self, 'preview_button') and self.preview_button.winfo_exists():
                 self.preview_button.configure(state=preview_state)
        except Exception as e: self._log(f"Warning: Could not update GUI state ({state}) - {e}")

    # Renamed for CTkTextbox
    def clear_preview_textbox(self):
        if hasattr(self, 'preview_textbox') and self.preview_textbox.winfo_exists():
            self.preview_textbox.configure(state=tk.NORMAL)
            self.preview_textbox.delete("1.0", tk.END)
            self.preview_textbox.configure(state=tk.DISABLED)

    # --- Threading Wrappers ---
    def start_embed_thread(self):
        if not self.input_image_path or not os.path.exists(self.input_image_path): messagebox.showerror("Error", "Please select valid input image."); return
        if not self.files_to_embed and not self.folders_to_embed:
            if not messagebox.askyesno("Confirm", "No files/folders selected.\nEmbed header only?"): return
        self.set_gui_state('disabled'); self.update_status("Embedding started...", "warning")
        thread = threading.Thread(target=self.embed_data_threaded, daemon=True); thread.start()

    def start_extract_thread(self):
        if not self.input_image_path or not os.path.exists(self.input_image_path): messagebox.showerror("Error", "Please select valid stego-image."); return
        self.set_gui_state('disabled'); self.update_status("Extraction started...", "warning")
        thread = threading.Thread(target=self.extract_data_threaded, daemon=True); thread.start()

    def start_preview_thread(self):
        if not self.input_image_path or not os.path.exists(self.input_image_path): messagebox.showerror("Error", "Please select valid stego-image."); return
        self.set_gui_state('disabled'); self.update_status("Previewing VFS contents...", "warning")
        self.clear_preview_textbox() # Use textbox clear
        print("[App] Starting preview thread...")
        thread = threading.Thread(target=self.preview_vfs_threaded, daemon=True); thread.start()

    # --- Thread Target Functions ---
    def embed_data_threaded(self):
        # (Uses QRNG flag, original success popup)
        output_stego_path = None; success = False
        try:
            base, ext = os.path.splitext(self.input_image_path); default_output_name = f"{os.path.basename(base)}_stego{ext or '.png'}"
            output_stego_path = filedialog.asksaveasfilename(parent=self.master, title="Save Stego Image As", initialfile=default_output_name, defaultextension=ext or ".png", filetypes=[("PNG Image", "*.png"), ("BMP Image", "*.bmp"), ("TIFF Image", "*.tiff"), ("All Files", "*.*")])
            if not output_stego_path: self.master.after(0, self.update_status, "Embedding cancelled.", "info"); return
            self.master.after(0, self.update_status, f"Embedding...", "warning")
            use_quantum = self.use_qrng_flag.get()
            success = self.stego_handler.embed(img_path=self.input_image_path, files_to_embed=self.files_to_embed,
                                               folders_to_embed=self.folders_to_embed, output_path=output_stego_path,
                                               use_qrng=use_quantum)
            if success:
                self.master.after(0, self.update_status, "Embedding successful!", "success")
                self.master.after(0, messagebox.showinfo, "Success", f"Data embedded successfully into:\n{output_stego_path}") # Original popup
        except Exception as e:
            success = False; error_msg = f"Embedding thread error: {e}"; self._log(error_msg); self._log(traceback.format_exc())
            self.master.after(0, self.update_status, f"Embedding error!", "error")
            self.master.after(0, messagebox.showerror, "Critical Error", f"Embedding error: {e}")
        finally:
             if not success and output_stego_path:
                  if 'error_msg' not in locals(): self.master.after(0, self.update_status, "Embedding failed (check console log).", "error")
             self.master.after(0, self.set_gui_state, 'normal')

    def extract_data_threaded(self):
        # (Uses original success popup)
        success = False
        try:
            output_dir = filedialog.askdirectory(parent=self.master, title="Select Directory to Extract Files To", mustexist=False)
            if not output_dir: self.master.after(0, self.update_status, "Extraction cancelled.", "info"); return
            self.master.after(0, self.update_status, f"Extracting...", "warning")
            success = self.stego_handler.extract(img_path=self.input_image_path, extract_to_dir=output_dir)
            if success:
                self.master.after(0, self.update_status, "Extraction successful!", "success")
                self.master.after(0, messagebox.showinfo, "Success", f"Data extracted successfully to:\n{output_dir}") # Original popup
        except Exception as e:
            success = False; error_msg = f"Extraction thread error: {e}"; self._log(error_msg); self._log(traceback.format_exc())
            self.master.after(0, self.update_status, f"Extraction error!", "error")
            self.master.after(0, messagebox.showerror, "Critical Error", f"Extraction error: {e}")
        finally:
             if not success:
                  if 'error_msg' not in locals(): self.master.after(0, self.update_status, "Extraction failed (check console log).", "error")
             self.master.after(0, self.set_gui_state, 'normal')

    def preview_vfs_threaded(self):
        # (Calls populate_preview_textbox)
        extracted_items = []
        try:
            print("[App Thread] Requesting payload bytes for preview...")
            payload_bytes = self.stego_handler.get_vfs_payload_bytes(self.input_image_path)
            print(f"[App Thread] Payload bytes received: {len(payload_bytes) if payload_bytes is not None else 'None'}")
            if payload_bytes is None: raise ValueError("Failed to retrieve payload bytes (returned None).")
            if not payload_bytes: self.master.after(0, self.update_status, "Preview: No payload found.", "info"); return
            vfs_stream = io.BytesIO(payload_bytes)
            self.master.after(0, self.update_status, "Parsing VFS archive...", "warning")
            try:
                with tarfile.open(fileobj=vfs_stream, mode="r:") as tar:
                    for member in tar.getmembers():
                         if member.name.startswith(("/", "\\")) or ".." in member.name.split(os.path.sep): self._log(f"Warning: Skipping unsafe path: {member.name}"); continue
                         member_type = "Folder" if member.isdir() else "File" if member.isfile() else "Other"
                         extracted_items.append({"name": member.name, "type": member_type})
                print(f"[App Thread] Parsed VFS, found {len(extracted_items)} items.")
            except tarfile.ReadError as tar_e: raise SteganographyError(f"Cannot read VFS archive: {tar_e}") from tar_e

            # Schedule populate_preview_textbox
            self.master.after(0, self.populate_preview_textbox, extracted_items) # Pass items
            self.master.after(0, self.update_status, f"Preview successful: {len(extracted_items)} items.", "success") # Original status update

        except (steganography.SteganographyError, tarfile.ReadError, ValueError) as e:
             error_msg = f"Preview Error: {e}"; self._log(error_msg)
             self.master.after(0, self.clear_preview_textbox) # Use textbox clear
             self.master.after(0, self.update_status, f"Preview error!", "error")
             self.master.after(0, messagebox.showerror, "Preview Error", error_msg)
        except Exception as e:
            error_msg = f"Unexpected Preview error: {e}"; self._log(error_msg); self._log(traceback.format_exc())
            self.master.after(0, self.clear_preview_textbox) # Use textbox clear
            self.master.after(0, self.update_status, f"Preview error!", "error")
            self.master.after(0, messagebox.showerror, "Critical Error", f"Preview error: {e}")
        finally:
            self.master.after(0, self.set_gui_state, 'normal')


    # *** Renamed and Rewritten for CTkTextbox ***
    # *** Includes DEBUG prints and default font ***
    def populate_preview_textbox(self, items):
        """Populates the preview Textbox with a formatted list of items."""
        print(f"[App Populate] Received {len(items)} items for Textbox.")
        try:
            self.clear_preview_textbox() # Clear previous content

            if not items:
                self.preview_textbox.configure(state=tk.NORMAL)
                self.preview_textbox.insert("1.0", "(VFS archive is empty or contains no listable items)")
                self.preview_textbox.configure(state=tk.DISABLED, text_color=COLORS['text_secondary'])
                print("[App Populate] No items to display.")
                return

            # Build the full string with indentation and icons
            full_text_list = []
            items.sort(key=lambda x: (0 if x['type'] == 'Folder' else 1, x['name'].lower()))
            indent_spaces = "    " # 4 spaces for indentation

            for item in items:
                clean_name = item['name'].replace('\\', '/').strip('/')
                if not clean_name: continue

                path_parts = clean_name.split('/')
                depth = len(path_parts) - 1
                indent_str = indent_spaces * depth

                icon = "📁" if item['type'] == "Folder" else "📄"
                display_name = path_parts[-1]
                # Format: Indent + Icon + Space + Name + Newline
                display_text = f"{indent_str}{icon}  {display_name}\n"
                full_text_list.append(display_text)

            full_text = "".join(full_text_list)
            print(f"[App Populate] Generated text (first 300 chars):\n{full_text[:300]}...")

            # Insert into textbox
            self.preview_textbox.configure(state=tk.NORMAL, text_color=COLORS['list_tree_fg']) # Ensure normal state and correct color
            self.preview_textbox.insert("1.0", full_text) # Insert at the beginning
            print("[App Populate] Text inserted into textbox.")
            self.preview_textbox.configure(state=tk.DISABLED) # Set back to read-only

            # Debug: Check content after insertion
            # Use after_idle to allow textbox to potentially render first
            self.master.after(10, lambda: print(f"[App Populate Debug] Textbox content length: {len(self.preview_textbox.get('1.0', tk.END).strip())}"))

        except Exception as e:
            print(f"[App Populate] Error populating textbox: {e}")
            traceback.print_exc()
            try:
                 self.preview_textbox.configure(state=tk.NORMAL)
                 self.preview_textbox.delete("1.0", tk.END)
                 self.preview_textbox.insert("1.0", f"Error populating preview:\n{e}")
                 self.preview_textbox.configure(state=tk.DISABLED, text_color=COLORS['error'])
            except: pass # Avoid errors within error handling


    def _log(self, message):
         print(f"[App] {message}")


def maximize_vertically(window, initial_width):
    """Attempts to maximize the window height while retaining width."""
    try:
        print("Attempting platform-specific maximize...")
        # Force window to appear and calculate sizes
        window.update_idletasks()
        screen_height = window.winfo_screenheight()
        screen_width = window.winfo_screenwidth()
        print(f"Screen: {screen_width}x{screen_height}")

        # Try platform-specific methods first (might maximize both ways)
        try:
            window.state('zoomed')
            print("Used state('zoomed')")
            # Check if width changed significantly, if so, revert it
            window.update_idletasks()
            if abs(window.winfo_width() - initial_width) > 100: # If width also maximized
                 print("Width also maximized, reverting width...")
                 window.geometry(f"{initial_width}x{window.winfo_height()}")
            return # Success or handled
        except tk.TclError:
            pass # Fall through if state('zoomed') fails

        try:
            # macOS specific (might also maximize both ways)
            window.attributes('-zoomed', True)
            print("Used attributes('-zoomed', True)")
            window.update_idletasks()
            if abs(window.winfo_width() - initial_width) > 100: # If width also maximized
                 print("Width also maximized, reverting width...")
                 window.geometry(f"{initial_width}x{window.winfo_height()}")
            return # Success or handled
        except tk.TclError:
            pass # Fall through if attributes('-zoomed', True) fails

        # Fallback: Set geometry manually to screen height
        print("Platform methods failed or not applicable, using manual geometry...")
        # Deduct a bit for taskbars/docks/menus
        y_offset = 100 # Adjust as needed for your OS
        target_height = screen_height - y_offset
        target_y = y_offset // 3 # Position slightly down from top
        window.geometry(f"{initial_width}x{target_height}+0+{target_y}")
        print(f"Set geometry manually: {initial_width}x{target_height}")

    except Exception as e:
         print(f"Could not automatically adjust window size: {e}")


if __name__ == "__main__":
    root = customtkinter.CTk()
    app = SteganoVFSApp(root)
    # Attempt maximize after a short delay
    root.after(200, lambda: maximize_vertically(root, app.initial_width))
    root.mainloop()